import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.firewall import (
    FirewallRule,
    Simulation,
    SimulationRuleSnapshot,
    SimulationRecordResult,
)
from app.schemas.firewall import (
    SimulationCreateRequest,
    SimulationSummaryResponse,
    SimulationDetailResponse,
    SimulationRuleSnapshotResponse,
    SimulationRecordResultResponse,
    PaginatedRecordResults,
)
from app.engine.firewall_engine import (
    FirewallRuleData,
    TrafficRecordData,
    evaluate_dataset,
)

router = APIRouter(prefix="/api/simulations", tags=["Simulations"])


@router.post("", response_model=SimulationSummaryResponse, status_code=status.HTTP_201_CREATED)
def run_simulation(req: SimulationCreateRequest, db: Session = Depends(get_db)):
    """
    Executes a simulation:
    1. Fetches current rules and creates a snapshot.
    2. Runs the evaluation engine.
    3. Persists simulation metadata, rule snapshots, and record decisions.
    """
    if not req.records:
        raise HTTPException(status_code=400, detail="Cannot run simulation without traffic records.")

    # 1. Fetch current rules sorted by priority ASC
    active_rules = db.query(FirewallRule).order_by(FirewallRule.priority.asc(), FirewallRule.id.asc()).all()
    
    # Name generation
    sim_count = db.query(Simulation).count()
    sim_name = req.simulation_name.strip() if (req.simulation_name and req.simulation_name.strip()) else f"Simulation #{sim_count + 1}"

    # Create simulation entry
    sim = Simulation(
        name=sim_name,
        total_records=len(req.records),
        valid_records=0,
        invalid_records=0,
        allowed_records=0,
        denied_records=0,
    )
    db.add(sim)
    db.flush()  # Generate sim.id

    # 2. Snapshot current rules
    rule_snapshots: List[SimulationRuleSnapshot] = []
    engine_rules: List[FirewallRuleData] = []
    
    for r in active_rules:
        snapshot = SimulationRuleSnapshot(
            simulation_id=sim.id,
            original_rule_id=r.id,
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
        rule_snapshots.append(snapshot)
        
        # Engine rule representation
        engine_rules.append(
            FirewallRuleData(
                id=r.id,
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
        )
    
    db.add_all(rule_snapshots)

    # 3. Convert input records to engine format
    engine_records = []
    for idx, rec in enumerate(req.records):
        rec_id = rec.record_id.strip() if rec.record_id and rec.record_id.strip() else f"rec-{idx + 1}"
        engine_records.append(
            TrafficRecordData(
                record_id=rec_id,
                source_ip=rec.source_ip.strip(),
                destination_ip=rec.destination_ip.strip(),
                destination_port=rec.destination_port.strip() if rec.destination_port else None,
                protocol=rec.protocol.strip(),
            )
        )

    # 4. Evaluate using the deterministic engine
    eval_results = evaluate_dataset(engine_records, engine_rules)

    # 5. Save results and calculate totals
    allowed_count = 0
    denied_count = 0
    invalid_count = 0
    valid_count = 0

    record_entities = []
    for res in eval_results:
        if res.validation_errors:
            invalid_count += 1
        else:
            valid_count += 1

        if res.decision == "ALLOW":
            allowed_count += 1
        else:
            denied_count += 1

        record_entities.append(
            SimulationRecordResult(
                simulation_id=sim.id,
                record_id=res.record_id,
                source_ip=res.source_ip,
                destination_ip=res.destination_ip,
                destination_port=res.destination_port,
                protocol=res.protocol,
                decision=res.decision,
                matched_rule_id=res.matched_rule_id,
                matched_rule_name=res.matched_rule_name,
                explanation=res.explanation,
                is_default_policy=res.is_default_policy,
                validation_errors="; ".join(res.validation_errors) if res.validation_errors else None,
            )
        )

    db.add_all(record_entities)

    sim.valid_records = valid_count
    sim.invalid_records = invalid_count
    sim.allowed_records = allowed_count
    sim.denied_records = denied_count

    db.commit()
    db.refresh(sim)
    return sim


@router.get("", response_model=List[SimulationSummaryResponse])
def list_simulations(db: Session = Depends(get_db)):
    """
    List all historical simulations sorted by newest first.
    """
    return db.query(Simulation).order_by(Simulation.created_at.desc(), Simulation.id.desc()).all()


@router.get("/{sim_id}", response_model=SimulationDetailResponse)
def get_simulation_detail(
    sim_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    decision: Optional[str] = Query(None, description="Filter by ALLOW or DENY"),
    matched_rule_id: Optional[str] = Query(None, description="Rule ID or 'default'"),
    protocol: Optional[str] = Query(None, description="TCP, UDP, ICMP"),
    search: Optional[str] = Query(None, description="Search by record ID, IP or rule name"),
    db: Session = Depends(get_db),
):
    """
    Get detailed simulation information, the rule snapshot used, and paginated records with filtering.
    """
    sim = db.query(Simulation).filter(Simulation.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation with ID {sim_id} not found")

    # Query records with filters
    q = db.query(SimulationRecordResult).filter(SimulationRecordResult.simulation_id == sim_id)

    if decision and decision.strip():
        q = q.filter(SimulationRecordResult.decision == decision.strip().upper())

    if protocol and protocol.strip():
        q = q.filter(SimulationRecordResult.protocol == protocol.strip().upper())

    if matched_rule_id and matched_rule_id.strip():
        clean_match = matched_rule_id.strip().lower()
        if clean_match == "default":
            q = q.filter(SimulationRecordResult.is_default_policy == True)
        else:
            try:
                rule_int = int(clean_match)
                q = q.filter(SimulationRecordResult.matched_rule_id == rule_int)
            except ValueError:
                pass

    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.filter(
            (SimulationRecordResult.record_id.ilike(term))
            | (SimulationRecordResult.source_ip.ilike(term))
            | (SimulationRecordResult.destination_ip.ilike(term))
            | (SimulationRecordResult.matched_rule_name.ilike(term))
        )

    total_filtered = q.count()
    total_pages = max(1, (total_filtered + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    items = q.order_by(SimulationRecordResult.id.asc()).offset(offset).limit(page_size).all()

    # Rule snapshots
    snapshots = (
        db.query(SimulationRuleSnapshot)
        .filter(SimulationRuleSnapshot.simulation_id == sim_id)
        .order_by(SimulationRuleSnapshot.priority.asc(), SimulationRuleSnapshot.id.asc())
        .all()
    )

    return SimulationDetailResponse(
        simulation=SimulationSummaryResponse.model_validate(sim),
        rules_snapshot=[SimulationRuleSnapshotResponse.model_validate(s) for s in snapshots],
        records=PaginatedRecordResults(
            items=[SimulationRecordResultResponse.model_validate(i) for i in items],
            total=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{sim_id}/export", response_class=PlainTextResponse)
def export_simulation_csv(sim_id: int, db: Session = Depends(get_db)):
    """
    Exports all record simulation decisions to CSV.
    """
    sim = db.query(Simulation).filter(Simulation.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation with ID {sim_id} not found")

    records = (
        db.query(SimulationRecordResult)
        .filter(SimulationRecordResult.simulation_id == sim_id)
        .order_by(SimulationRecordResult.id.asc())
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
        "Decision",
        "Matched Rule ID",
        "Matched Rule Name",
        "Is Default Policy",
        "Explanation",
        "Validation Errors",
    ])

    for r in records:
        writer.writerow([
            r.record_id,
            r.source_ip,
            r.destination_ip,
            r.destination_port or "",
            r.protocol,
            r.decision,
            r.matched_rule_id if r.matched_rule_id is not None else "N/A",
            r.matched_rule_name or "None",
            "YES" if r.is_default_policy else "NO",
            r.explanation,
            r.validation_errors or "",
        ])

    sanitized_name = "".join(c if c.isalnum() else "_" for c in sim.name)
    filename = f"boho_simulation_{sim.id}_{sanitized_name}.csv"

    return PlainTextResponse(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/{sim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_simulation(sim_id: int, db: Session = Depends(get_db)):
    """
    Delete a historical simulation.
    """
    sim = db.query(Simulation).filter(Simulation.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation with ID {sim_id} not found")

    db.delete(sim)
    db.commit()
    return None
