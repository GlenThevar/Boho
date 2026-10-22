import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.firewall import Simulation, SimulationRecordResult, SimulationRuleSnapshot
from app.models.analysis import (
    PolicyComparison,
    PolicyComparisonRuleSnapshot,
    PolicyComparisonRecordResult,
)
from app.schemas.analysis import (
    PolicyComparisonCreateRequest,
    PolicyComparisonSummaryResponse,
    PolicyComparisonDetailResponse,
    PolicyComparisonRecordResponse,
    PaginatedComparisonRecords,
    ComparisonRuleSnapshotItem,
)
from app.engine.firewall_engine import (
    FirewallRuleData,
    TrafficRecordData,
    evaluate_dataset,
    validate_rule,
)

router = APIRouter(prefix="/api/comparisons", tags=["Policy Comparisons"])


@router.post("", response_model=PolicyComparisonSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_policy_comparison(req: PolicyComparisonCreateRequest, db: Session = Depends(get_db)):
    """
    Creates a Before-and-After policy comparison:
    1. Loads the original simulation and its recorded traffic dataset.
    2. Snapshots original rules and proposed rules.
    3. Re-evaluates identical traffic records against the proposed rules using the evaluation engine.
    4. Computes differences, counts, and reasons.
    5. Preserves historical reproducibility.
    """
    # 1. Fetch original simulation
    sim = db.query(Simulation).filter(Simulation.id == req.simulation_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation with ID {req.simulation_id} not found")

    # Fetch original evaluated records
    original_records = (
        db.query(SimulationRecordResult)
        .filter(SimulationRecordResult.simulation_id == req.simulation_id)
        .order_by(SimulationRecordResult.id.asc())
        .all()
    )

    if not original_records:
        raise HTTPException(status_code=400, detail="Original simulation contains no recorded traffic packets.")

    # 2. Validate proposed rules
    proposed_engine_rules: List[FirewallRuleData] = []
    for idx, r in enumerate(req.proposed_rules):
        p_data = FirewallRuleData(
            id=idx + 1,
            name=r.name,
            priority=r.priority,
            source_ip=r.source_ip,
            destination_ip=r.destination_ip,
            destination_port=r.destination_port,
            protocol=r.protocol,
            action=r.action,
            enabled=r.enabled,
            description=r.description,
        )
        val_errs = validate_rule(p_data)
        if val_errs:
            raise HTTPException(
                status_code=422,
                detail=f"Proposed Rule #{r.priority} '{r.name}' is invalid: {'; '.join(val_errs)}"
            )
        proposed_engine_rules.append(p_data)

    # 3. Convert original records to engine format
    traffic_inputs = [
        TrafficRecordData(
            record_id=rec.record_id,
            source_ip=rec.source_ip,
            destination_ip=rec.destination_ip,
            destination_port=rec.destination_port,
            protocol=rec.protocol,
        )
        for rec in original_records
    ]

    # 4. Evaluate against proposed rules using the firewall evaluation engine
    proposed_results = evaluate_dataset(traffic_inputs, proposed_engine_rules)

    # 5. Calculate diffs
    comp_name = req.name.strip() if (req.name and req.name.strip()) else f"Comparison vs {sim.name}"
    
    comp = PolicyComparison(
        simulation_id=sim.id,
        name=comp_name,
        original_allowed=sim.allowed_records,
        proposed_allowed=0,
        original_denied=sim.denied_records,
        proposed_denied=0,
        total_records=len(original_records),
        changed_decisions=0,
        allow_to_deny=0,
        deny_to_allow=0,
        rule_changes_only=0,
    )
    db.add(comp)
    db.flush()

    # Snapshot original rules
    original_snapshots = (
        db.query(SimulationRuleSnapshot)
        .filter(SimulationRuleSnapshot.simulation_id == sim.id)
        .order_by(SimulationRuleSnapshot.priority.asc())
        .all()
    )
    for orig in original_snapshots:
        db.add(
            PolicyComparisonRuleSnapshot(
                comparison_id=comp.id,
                snapshot_type="ORIGINAL",
                original_rule_id=orig.original_rule_id or orig.id,
                name=orig.name,
                priority=orig.priority,
                source_ip=orig.source_ip,
                destination_ip=orig.destination_ip,
                destination_port=orig.destination_port,
                protocol=orig.protocol,
                action=orig.action,
                enabled=orig.enabled,
                description=orig.description,
            )
        )

    # Snapshot proposed rules
    for prop in proposed_engine_rules:
        db.add(
            PolicyComparisonRuleSnapshot(
                comparison_id=comp.id,
                snapshot_type="PROPOSED",
                original_rule_id=None,
                name=prop.name,
                priority=prop.priority,
                source_ip=prop.source_ip,
                destination_ip=prop.destination_ip,
                destination_port=prop.destination_port,
                protocol=prop.protocol,
                action=prop.action,
                enabled=prop.enabled,
                description=prop.description,
            )
        )

    # Record-level comparison results
    prop_allowed = 0
    prop_denied = 0
    changed_decisions = 0
    allow_to_deny = 0
    deny_to_allow = 0
    rule_changes_only = 0

    record_entities = []
    for orig, prop in zip(original_records, proposed_results):
        if prop.decision == "ALLOW":
            prop_allowed += 1
        else:
            prop_denied += 1

        # Classify change
        if orig.decision == "ALLOW" and prop.decision == "DENY":
            change_type = "ALLOW_TO_DENY"
            changed_decisions += 1
            allow_to_deny += 1
            explanation = (
                f"Decision changed from ALLOW to DENY. Previously permitted by '{orig.matched_rule_name or 'Rule'}'; "
                f"under proposed policy: {prop.explanation}"
            )
        elif orig.decision == "DENY" and prop.decision == "ALLOW":
            change_type = "DENY_TO_ALLOW"
            changed_decisions += 1
            deny_to_allow += 1
            explanation = (
                f"Decision changed from DENY to ALLOW. Previously denied ({orig.matched_rule_name or 'Default Policy'}); "
                f"under proposed policy: Matched Rule '{prop.matched_rule_name}' (Action: ALLOW)."
            )
        elif orig.decision == prop.decision:
            if orig.matched_rule_name != prop.matched_rule_name or orig.is_default_policy != prop.is_default_policy:
                change_type = "SAME_DECISION_DIFFERENT_RULE"
                rule_changes_only += 1
                explanation = (
                    f"Final decision remained {orig.decision}, but matched rule shifted from "
                    f"'{orig.matched_rule_name or 'Default DENY'}' to '{prop.matched_rule_name or 'Default DENY'}'. "
                    f"{prop.explanation}"
                )
            else:
                change_type = "UNCHANGED"
                explanation = f"No change. Decision remains {orig.decision} via '{orig.matched_rule_name or 'Default DENY'}'."
        else:
            change_type = "UNCHANGED"
            explanation = "Decision unchanged."

        record_entities.append(
            PolicyComparisonRecordResult(
                comparison_id=comp.id,
                record_id=orig.record_id,
                source_ip=orig.source_ip,
                destination_ip=orig.destination_ip,
                destination_port=orig.destination_port,
                protocol=orig.protocol,
                original_decision=orig.decision,
                proposed_decision=prop.decision,
                original_rule_id=orig.matched_rule_id,
                original_rule_name=orig.matched_rule_name,
                proposed_rule_id=prop.matched_rule_id,
                proposed_rule_name=prop.matched_rule_name,
                change_type=change_type,
                explanation=explanation,
            )
        )

    db.add_all(record_entities)

    comp.proposed_allowed = prop_allowed
    comp.proposed_denied = prop_denied
    comp.changed_decisions = changed_decisions
    comp.allow_to_deny = allow_to_deny
    comp.deny_to_allow = deny_to_allow
    comp.rule_changes_only = rule_changes_only

    db.commit()
    db.refresh(comp)
    return comp


@router.get("", response_model=List[PolicyComparisonSummaryResponse])
def list_policy_comparisons(db: Session = Depends(get_db)):
    """
    List all historical policy comparisons.
    """
    return db.query(PolicyComparison).order_by(PolicyComparison.created_at.desc(), PolicyComparison.id.desc()).all()


@router.get("/{comp_id}", response_model=PolicyComparisonDetailResponse)
def get_policy_comparison_detail(
    comp_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    change_type: Optional[str] = Query(None, description="Filter: CHANGED_ONLY, ALLOW_TO_DENY, DENY_TO_ALLOW, SAME_DECISION_DIFFERENT_RULE, UNCHANGED"),
    search: Optional[str] = Query(None, description="Search record ID or IPs"),
    db: Session = Depends(get_db),
):
    """
    Get detailed comparison summary, snapshots, and paginated records.
    """
    comp = db.query(PolicyComparison).filter(PolicyComparison.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Policy comparison with ID {comp_id} not found")

    q = db.query(PolicyComparisonRecordResult).filter(PolicyComparisonRecordResult.comparison_id == comp_id)

    if change_type and change_type.strip():
        ct = change_type.strip().upper()
        if ct == "CHANGED_ONLY":
            q = q.filter(PolicyComparisonRecordResult.change_type.in_(["ALLOW_TO_DENY", "DENY_TO_ALLOW"]))
        else:
            q = q.filter(PolicyComparisonRecordResult.change_type == ct)

    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.filter(
            (PolicyComparisonRecordResult.record_id.ilike(term)) |
            (PolicyComparisonRecordResult.source_ip.ilike(term)) |
            (PolicyComparisonRecordResult.destination_ip.ilike(term))
        )

    total_filtered = q.count()
    total_pages = max(1, (total_filtered + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    items = q.order_by(PolicyComparisonRecordResult.id.asc()).offset(offset).limit(page_size).all()

    # Rule snapshots
    snapshots = (
        db.query(PolicyComparisonRuleSnapshot)
        .filter(PolicyComparisonRuleSnapshot.comparison_id == comp_id)
        .order_by(PolicyComparisonRuleSnapshot.priority.asc())
        .all()
    )

    orig_snapshots = [s for s in snapshots if s.snapshot_type == "ORIGINAL"]
    prop_snapshots = [s for s in snapshots if s.snapshot_type == "PROPOSED"]

    return PolicyComparisonDetailResponse(
        comparison=PolicyComparisonSummaryResponse.model_validate(comp),
        original_rules=[ComparisonRuleSnapshotItem.model_validate(s) for s in orig_snapshots],
        proposed_rules=[ComparisonRuleSnapshotItem.model_validate(s) for s in prop_snapshots],
        records=PaginatedComparisonRecords(
            items=[PolicyComparisonRecordResponse.model_validate(i) for i in items],
            total=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{comp_id}/export", response_class=PlainTextResponse)
def export_comparison_csv(comp_id: int, db: Session = Depends(get_db)):
    """
    Exports full comparison dataset to CSV.
    """
    comp = db.query(PolicyComparison).filter(PolicyComparison.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Policy comparison with ID {comp_id} not found")

    records = (
        db.query(PolicyComparisonRecordResult)
        .filter(PolicyComparisonRecordResult.comparison_id == comp_id)
        .order_by(PolicyComparisonRecordResult.id.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID",
        "Source IP",
        "Destination IP",
        "Destination Port",
        "Protocol",
        "Original Decision",
        "Proposed Decision",
        "Original Matched Rule",
        "Proposed Matched Rule",
        "Change Classification",
        "Detailed Explanation",
    ])

    for r in records:
        writer.writerow([
            r.record_id,
            r.source_ip,
            r.destination_ip,
            r.destination_port or "",
            r.protocol,
            r.original_decision,
            r.proposed_decision,
            r.original_rule_name or "Default DENY",
            r.proposed_rule_name or "Default DENY",
            r.change_type,
            r.explanation,
        ])

    sanitized = "".join(c if c.isalnum() else "_" for c in comp.name)
    filename = f"boho_policy_comparison_{comp.id}_{sanitized}.csv"

    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/{comp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comparison(comp_id: int, db: Session = Depends(get_db)):
    """
    Deletes a historical policy comparison.
    """
    comp = db.query(PolicyComparison).filter(PolicyComparison.id == comp_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail=f"Policy comparison with ID {comp_id} not found")

    db.delete(comp)
    db.commit()
    return None
