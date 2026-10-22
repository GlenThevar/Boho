import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class PolicyAnalysis(Base):
    __tablename__ = "policy_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(String(32), default="COMPLETED", nullable=False)
    rules_analyzed_count = Column(Integer, default=0, nullable=False)
    shadowed_count = Column(Integer, default=0, nullable=False)
    redundant_count = Column(Integer, default=0, nullable=False)
    findings_count = Column(Integer, default=0, nullable=False)

    rules_snapshot = relationship(
        "PolicyAnalysisRuleSnapshot",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="PolicyAnalysisRuleSnapshot.priority"
    )
    findings = relationship(
        "SecurityFinding",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )


class PolicyAnalysisRuleSnapshot(Base):
    __tablename__ = "policy_analysis_rule_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("policy_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    original_rule_id = Column(Integer, nullable=True)
    name = Column(String(120), nullable=False)
    priority = Column(Integer, nullable=False)
    source_ip = Column(String(64), nullable=False)
    destination_ip = Column(String(64), nullable=False)
    destination_port = Column(String(32), nullable=False)
    protocol = Column(String(16), nullable=False)
    action = Column(String(16), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

    analysis = relationship("PolicyAnalysis", back_populates="rules_snapshot")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("policy_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_code = Column(String(120), nullable=False, index=True)
    rule_id = Column(Integer, nullable=True)
    rule_name = Column(String(120), nullable=False)
    rule_priority = Column(Integer, nullable=False)
    category = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False, index=True)  # Critical, High, Medium, Low
    finding_type = Column(String(32), nullable=False, index=True)  # SECURITY_RISK, SHADOWING, REDUNDANCY
    title = Column(String(200), nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=True)
    remediation = Column(Text, nullable=False)
    confidence = Column(String(32), default="Confirmed", nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False, index=True)
    dismissed_reason = Column(Text, nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)

    analysis = relationship("PolicyAnalysis", back_populates="findings")


class PolicyComparison(Base):
    __tablename__ = "policy_comparisons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    name = Column(String(150), nullable=False)
    original_allowed = Column(Integer, default=0, nullable=False)
    proposed_allowed = Column(Integer, default=0, nullable=False)
    original_denied = Column(Integer, default=0, nullable=False)
    proposed_denied = Column(Integer, default=0, nullable=False)
    total_records = Column(Integer, default=0, nullable=False)
    changed_decisions = Column(Integer, default=0, nullable=False)
    allow_to_deny = Column(Integer, default=0, nullable=False)
    deny_to_allow = Column(Integer, default=0, nullable=False)
    rule_changes_only = Column(Integer, default=0, nullable=False)

    simulation = relationship("Simulation")
    rules_snapshot = relationship(
        "PolicyComparisonRuleSnapshot",
        back_populates="comparison",
        cascade="all, delete-orphan"
    )
    records = relationship(
        "PolicyComparisonRecordResult",
        back_populates="comparison",
        cascade="all, delete-orphan"
    )


class PolicyComparisonRuleSnapshot(Base):
    __tablename__ = "policy_comparison_rule_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comparison_id = Column(Integer, ForeignKey("policy_comparisons.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_type = Column(String(16), nullable=False)  # ORIGINAL or PROPOSED
    original_rule_id = Column(Integer, nullable=True)
    name = Column(String(120), nullable=False)
    priority = Column(Integer, nullable=False)
    source_ip = Column(String(64), nullable=False)
    destination_ip = Column(String(64), nullable=False)
    destination_port = Column(String(32), nullable=False)
    protocol = Column(String(16), nullable=False)
    action = Column(String(16), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)

    comparison = relationship("PolicyComparison", back_populates="rules_snapshot")


class PolicyComparisonRecordResult(Base):
    __tablename__ = "policy_comparison_record_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comparison_id = Column(Integer, ForeignKey("policy_comparisons.id", ondelete="CASCADE"), nullable=False, index=True)
    record_id = Column(String(64), nullable=False, index=True)
    source_ip = Column(String(64), nullable=False)
    destination_ip = Column(String(64), nullable=False)
    destination_port = Column(String(32), nullable=True)
    protocol = Column(String(16), nullable=False)
    original_decision = Column(String(16), nullable=False)
    proposed_decision = Column(String(16), nullable=False)
    original_rule_id = Column(Integer, nullable=True)
    original_rule_name = Column(String(120), nullable=True)
    proposed_rule_id = Column(Integer, nullable=True)
    proposed_rule_name = Column(String(120), nullable=True)
    change_type = Column(String(32), nullable=False, index=True)  # ALLOW_TO_DENY, DENY_TO_ALLOW, SAME_DECISION_DIFFERENT_RULE, UNCHANGED
    explanation = Column(Text, nullable=False)

    comparison = relationship("PolicyComparison", back_populates="records")
