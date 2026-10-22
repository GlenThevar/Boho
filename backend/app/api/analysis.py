from datetime import datetime, timezone
import json
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.firewall import FirewallRule
from app.models.analysis import (
    PolicyAnalysis,
    PolicyAnalysisRuleSnapshot,
    SecurityFinding,
)
from app.schemas.analysis import (
    PolicyAnalysisSummaryResponse,
    PolicyAnalysisDetailResponse,
    PolicyAnalysisRuleSnapshotResponse,
    SecurityFindingResponse,
    DismissFindingRequest,
)
from app.engine.firewall_engine import FirewallRuleData
from app.engine.policy_analyzer import analyze_firewall_policy

router = APIRouter(prefix="/api/analysis", tags=["Policy Analysis"])


def format_finding_response(f: SecurityFinding) -> SecurityFindingResponse:
    ev = None
    if f.evidence_json:
        try:
            ev = json.loads(f.evidence_json)
        except Exception:
            ev = {"raw": f.evidence_json}
    
    return SecurityFindingResponse(
        id=f.id,
        analysis_id=f.analysis_id,
        finding_code=f.finding_code,
        rule_id=f.rule_id,
        rule_name=f.rule_name,
        rule_priority=f.rule_priority,
        category=f.category,
        severity=f.severity,
        finding_type=f.finding_type,
        title=f.title,
        explanation=f.explanation,
        evidence=ev,
        remediation=f.remediation,
        confidence=f.confidence,
        is_dismissed=f.is_dismissed,
        dismissed_reason=f.dismissed_reason,
        dismissed_at=f.dismissed_at,
    )


def compute_analysis_summary(analysis: PolicyAnalysis) -> PolicyAnalysisSummaryResponse:
    sev_dist: Dict[str, int] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    cat_dist: Dict[str, int] = {}
    
    for f in analysis.findings:
        if not f.is_dismissed:
            sev_dist[f.severity] = sev_dist.get(f.severity, 0) + 1
            cat_dist[f.category] = cat_dist.get(f.category, 0) + 1

    return PolicyAnalysisSummaryResponse(
        id=analysis.id,
        created_at=analysis.created_at,
        status=analysis.status,
        rules_analyzed_count=analysis.rules_analyzed_count,
        shadowed_count=analysis.shadowed_count,
        redundant_count=analysis.redundant_count,
        findings_count=analysis.findings_count,
        severity_distribution=sev_dist,
        category_distribution=cat_dist,
    )


@router.post("/run", response_model=PolicyAnalysisSummaryResponse, status_code=status.HTTP_201_CREATED)
def run_policy_analysis(db: Session = Depends(get_db)):
    """
    Executes a comprehensive policy audit:
    - Analyzes enabled rules for shadowing, redundancy, and security risks.
    - Preserves historical dismissals ONLY if the relevant rule and finding match.
    - Saves analysis snapshot and findings.
    """
    active_rules = db.query(FirewallRule).order_by(FirewallRule.priority.asc(), FirewallRule.id.asc()).all()

    # Convert to engine data structures
    engine_rules: List[FirewallRuleData] = [
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
        for r in active_rules
    ]

    # Run analysis engine
    report = analyze_firewall_policy(engine_rules)

    # Check for previously dismissed findings for identical rules
    latest_analysis = db.query(PolicyAnalysis).order_by(PolicyAnalysis.created_at.desc()).first()
    previous_dismissals: Dict[str, tuple] = {}  # finding_code -> (reason, at)
    if latest_analysis:
        for old_f in latest_analysis.findings:
            if old_f.is_dismissed:
                # Find corresponding rule in old snapshot
                old_snapshot = db.query(PolicyAnalysisRuleSnapshot).filter(
                    PolicyAnalysisRuleSnapshot.analysis_id == latest_analysis.id,
                    PolicyAnalysisRuleSnapshot.original_rule_id == old_f.rule_id
                ).first()

                # Find corresponding rule in current rules
                cur_rule = next((r for r in active_rules if r.id == old_f.rule_id), None)

                # Only carry forward dismissal if the rule's definition has NOT changed
                if old_snapshot and cur_rule:
                    same_definition = (
                        old_snapshot.name == cur_rule.name and
                        old_snapshot.priority == cur_rule.priority and
                        old_snapshot.source_ip == cur_rule.source_ip and
                        old_snapshot.destination_ip == cur_rule.destination_ip and
                        old_snapshot.destination_port == cur_rule.destination_port and
                        old_snapshot.protocol == cur_rule.protocol and
                        old_snapshot.action == cur_rule.action and
                        old_snapshot.enabled == cur_rule.enabled
                    )
                    if same_definition:
                        previous_dismissals[old_f.finding_code] = (old_f.dismissed_reason, old_f.dismissed_at)

    # Create new PolicyAnalysis record
    analysis = PolicyAnalysis(
        status="COMPLETED",
        rules_analyzed_count=report.rules_analyzed_count,
        shadowed_count=len(report.shadowed_rules),
        redundant_count=len(report.redundant_rules),
        findings_count=len(report.security_findings),
    )
    db.add(analysis)
    db.flush()

    # Snapshot rules
    snapshots = [
        PolicyAnalysisRuleSnapshot(
            analysis_id=analysis.id,
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
        for r in active_rules
    ]
    db.add_all(snapshots)

    # Persist findings
    finding_entities = []
    for f in report.security_findings:
        is_dism = False
        d_reason = None
        d_at = None
        if f.finding_code in previous_dismissals:
            is_dism = True
            d_reason, d_at = previous_dismissals[f.finding_code]

        finding_entities.append(
            SecurityFinding(
                analysis_id=analysis.id,
                finding_code=f.finding_code,
                rule_id=f.rule_id,
                rule_name=f.rule_name,
                rule_priority=f.rule_priority,
                category=f.category,
                severity=f.severity,
                finding_type=f.finding_type,
                title=f.title,
                explanation=f.explanation,
                evidence_json=json.dumps(f.evidence),
                remediation=f.remediation,
                confidence=f.confidence,
                is_dismissed=is_dism,
                dismissed_reason=d_reason,
                dismissed_at=d_at,
            )
        )

    db.add_all(finding_entities)
    db.commit()
    db.refresh(analysis)

    return compute_analysis_summary(analysis)


@router.get("/latest", response_model=PolicyAnalysisDetailResponse)
def get_latest_policy_analysis(db: Session = Depends(get_db)):
    """
    Retrieves the most recent policy analysis. If none exists, runs one on current rules.
    """
    analysis = db.query(PolicyAnalysis).order_by(PolicyAnalysis.created_at.desc(), PolicyAnalysis.id.desc()).first()
    if not analysis:
        # Auto-run an analysis so user sees immediate results
        return run_policy_analysis_and_return_detail(db)

    return get_analysis_detail(analysis.id, db)


def run_policy_analysis_and_return_detail(db: Session) -> PolicyAnalysisDetailResponse:
    run_policy_analysis(db)
    analysis = db.query(PolicyAnalysis).order_by(PolicyAnalysis.created_at.desc()).first()
    return get_analysis_detail(analysis.id, db)


@router.get("", response_model=List[PolicyAnalysisSummaryResponse])
def list_policy_analyses(db: Session = Depends(get_db)):
    """
    List all historical policy analyses.
    """
    analyses = db.query(PolicyAnalysis).order_by(PolicyAnalysis.created_at.desc()).all()
    return [compute_analysis_summary(a) for a in analyses]


@router.get("/{analysis_id}", response_model=PolicyAnalysisDetailResponse)
def get_analysis_detail(analysis_id: int, db: Session = Depends(get_db)):
    """
    Returns full details, rule snapshot, and findings for a specific analysis session.
    """
    analysis = db.query(PolicyAnalysis).filter(PolicyAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Policy analysis with ID {analysis_id} not found")

    snapshots = (
        db.query(PolicyAnalysisRuleSnapshot)
        .filter(PolicyAnalysisRuleSnapshot.analysis_id == analysis_id)
        .order_by(PolicyAnalysisRuleSnapshot.priority.asc())
        .all()
    )

    findings = (
        db.query(SecurityFinding)
        .filter(SecurityFinding.analysis_id == analysis_id)
        .order_by(SecurityFinding.id.asc())
        .all()
    )

    return PolicyAnalysisDetailResponse(
        analysis=compute_analysis_summary(analysis),
        rules_snapshot=[PolicyAnalysisRuleSnapshotResponse.model_validate(s) for s in snapshots],
        findings=[format_finding_response(f) for f in findings],
    )


@router.patch("/findings/{finding_id}/dismiss", response_model=SecurityFindingResponse)
def dismiss_finding(finding_id: int, req: DismissFindingRequest, db: Session = Depends(get_db)):
    """
    Dismisses a security finding with a mandatory reason.
    Does NOT alter the underlying firewall rule.
    """
    finding = db.query(SecurityFinding).filter(SecurityFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Security finding with ID {finding_id} not found")

    finding.is_dismissed = True
    finding.dismissed_reason = req.reason.strip()
    finding.dismissed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(finding)
    return format_finding_response(finding)


@router.patch("/findings/{finding_id}/restore", response_model=SecurityFindingResponse)
def restore_finding(finding_id: int, db: Session = Depends(get_db)):
    """
    Restores a previously dismissed security finding back to active status.
    """
    finding = db.query(SecurityFinding).filter(SecurityFinding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Security finding with ID {finding_id} not found")

    finding.is_dismissed = False
    finding.dismissed_reason = None
    finding.dismissed_at = None

    db.commit()
    db.refresh(finding)
    return format_finding_response(finding)
