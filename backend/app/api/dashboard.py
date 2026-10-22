from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.firewall import Simulation, SimulationRecordResult
from app.schemas.firewall import (
    DashboardStatsResponse,
    SimulationSummaryResponse,
    RuleMatchStat,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Computes real aggregated metrics across all simulations for the dashboard.
    """
    total_sims = db.query(Simulation).count()
    
    # Aggregates from Simulation table
    totals = db.query(
        func.coalesce(func.sum(Simulation.total_records), 0).label("total_records"),
        func.coalesce(func.sum(Simulation.valid_records), 0).label("valid_records"),
        func.coalesce(func.sum(Simulation.invalid_records), 0).label("invalid_records"),
        func.coalesce(func.sum(Simulation.allowed_records), 0).label("allowed_records"),
        func.coalesce(func.sum(Simulation.denied_records), 0).label("denied_records"),
    ).first()

    total_records = int(totals.total_records) if totals else 0
    invalid_records = int(totals.invalid_records) if totals else 0
    allowed_records = int(totals.allowed_records) if totals else 0
    denied_records = int(totals.denied_records) if totals else 0

    allowed_pct = round((allowed_records / total_records * 100), 1) if total_records > 0 else 0.0
    denied_pct = round((denied_records / total_records * 100), 1) if total_records > 0 else 0.0

    # Rule match distribution from SimulationRecordResult
    # Group by matched_rule_id, matched_rule_name, decision
    match_query = (
        db.query(
            SimulationRecordResult.matched_rule_id,
            SimulationRecordResult.matched_rule_name,
            SimulationRecordResult.decision,
            func.count(SimulationRecordResult.id).label("count")
        )
        .group_by(
            SimulationRecordResult.matched_rule_id,
            SimulationRecordResult.matched_rule_name,
            SimulationRecordResult.decision
        )
        .order_by(func.count(SimulationRecordResult.id).desc())
        .limit(10)
        .all()
    )

    rule_match_stats: List[RuleMatchStat] = []
    for r in match_query:
        name = r.matched_rule_name if r.matched_rule_name else "Default Policy (No Rule Match)"
        rule_match_stats.append(
            RuleMatchStat(
                rule_id=r.matched_rule_id,
                rule_name=name,
                match_count=r.count,
                action=r.decision
            )
        )

    # 5 most recent simulations
    recent_sims = (
        db.query(Simulation)
        .order_by(Simulation.created_at.desc(), Simulation.id.desc())
        .limit(5)
        .all()
    )

    return DashboardStatsResponse(
        total_simulations=total_sims,
        total_records=total_records,
        allowed_records=allowed_records,
        allowed_percentage=allowed_pct,
        denied_records=denied_records,
        denied_percentage=denied_pct,
        invalid_records=invalid_records,
        rule_match_stats=rule_match_stats,
        recent_simulations=[SimulationSummaryResponse.model_validate(s) for s in recent_sims]
    )
