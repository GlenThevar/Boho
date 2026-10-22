import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class FirewallRule(Base):
    __tablename__ = "firewall_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    priority = Column(Integer, nullable=False, index=True)
    source_ip = Column(String(64), nullable=False)
    destination_ip = Column(String(64), nullable=False)
    destination_port = Column(String(32), nullable=False)
    protocol = Column(String(16), nullable=False)  # TCP, UDP, ICMP, ANY
    action = Column(String(16), nullable=False)    # ALLOW, DENY
    enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    total_records = Column(Integer, default=0, nullable=False)
    valid_records = Column(Integer, default=0, nullable=False)
    invalid_records = Column(Integer, default=0, nullable=False)
    allowed_records = Column(Integer, default=0, nullable=False)
    denied_records = Column(Integer, default=0, nullable=False)

    rules_snapshot = relationship(
        "SimulationRuleSnapshot",
        back_populates="simulation",
        cascade="all, delete-orphan",
        order_by="SimulationRuleSnapshot.priority"
    )
    records = relationship(
        "SimulationRecordResult",
        back_populates="simulation",
        cascade="all, delete-orphan"
    )


class SimulationRuleSnapshot(Base):
    __tablename__ = "simulation_rule_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
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

    simulation = relationship("Simulation", back_populates="rules_snapshot")


class SimulationRecordResult(Base):
    __tablename__ = "simulation_record_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
    record_id = Column(String(64), nullable=False, index=True)
    source_ip = Column(String(64), nullable=False)
    destination_ip = Column(String(64), nullable=False)
    destination_port = Column(String(32), nullable=True)
    protocol = Column(String(16), nullable=False)
    decision = Column(String(16), nullable=False, index=True)  # ALLOW, DENY
    matched_rule_id = Column(Integer, nullable=True)
    matched_rule_name = Column(String(120), nullable=True)
    explanation = Column(Text, nullable=False)
    is_default_policy = Column(Boolean, default=False, nullable=False)
    validation_errors = Column(Text, nullable=True)

    simulation = relationship("Simulation", back_populates="records")
