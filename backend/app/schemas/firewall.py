from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.engine.firewall_engine import (
    validate_ip_or_cidr,
    validate_port_spec,
    validate_protocol_spec,
)


class FirewallRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Rule display name")
    priority: int = Field(..., ge=1, description="Evaluation priority (1 = highest)")
    source_ip: str = Field(..., description="IPv4/IPv6 address, CIDR range, or 'ANY'")
    destination_ip: str = Field(..., description="IPv4/IPv6 address, CIDR range, or 'ANY'")
    destination_port: str = Field(..., description="Single port (1-65535), range 'start-end', or 'ANY'")
    protocol: str = Field(..., description="TCP, UDP, ICMP, or ANY")
    action: str = Field(..., description="ALLOW or DENY")
    enabled: bool = Field(default=True, description="Whether rule is active in evaluations")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description")

    @field_validator("source_ip")
    @classmethod
    def check_source_ip(cls, v: str) -> str:
        ok, err, _ = validate_ip_or_cidr(v, "Source IP")
        if not ok:
            raise ValueError(err)
        return v.strip().upper() if v.strip().upper() == "ANY" else v.strip()

    @field_validator("destination_ip")
    @classmethod
    def check_destination_ip(cls, v: str) -> str:
        ok, err, _ = validate_ip_or_cidr(v, "Destination IP")
        if not ok:
            raise ValueError(err)
        return v.strip().upper() if v.strip().upper() == "ANY" else v.strip()

    @field_validator("protocol")
    @classmethod
    def check_protocol(cls, v: str) -> str:
        ok, err = validate_protocol_spec(v)
        if not ok:
            raise ValueError(err)
        return v.strip().upper()

    @field_validator("destination_port")
    @classmethod
    def check_destination_port(cls, v: str, info) -> str:
        proto = info.data.get("protocol", "ANY")
        ok, err = validate_port_spec(v, proto)
        if not ok:
            raise ValueError(err)
        return v.strip().upper() if v.strip().upper() == "ANY" else v.strip()

    @field_validator("action")
    @classmethod
    def check_action(cls, v: str) -> str:
        action_clean = v.strip().upper()
        if action_clean not in {"ALLOW", "DENY"}:
            raise ValueError(f"Action must be either 'ALLOW' or 'DENY', received '{v}'")
        return action_clean


class FirewallRuleCreate(FirewallRuleBase):
    pass


class FirewallRuleUpdate(FirewallRuleBase):
    pass


class FirewallRuleToggle(BaseModel):
    enabled: bool


class FirewallRuleReorderItem(BaseModel):
    id: int
    priority: int = Field(..., ge=1)


class FirewallRuleResponse(FirewallRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TrafficRecordInput(BaseModel):
    record_id: Optional[str] = None
    source_ip: str
    destination_ip: str
    destination_port: Optional[str] = None
    protocol: str = "TCP"


class ValidationIssue(BaseModel):
    row_number: int
    record_id: str
    errors: List[str]


class TrafficPreviewResponse(BaseModel):
    total_records: int
    valid_count: int
    invalid_count: int
    preview_records: List[dict]
    validation_issues: List[ValidationIssue]
    file_warning: Optional[str] = None


class SimulationCreateRequest(BaseModel):
    simulation_name: Optional[str] = None
    records: List[TrafficRecordInput]


class SimulationRuleSnapshotResponse(BaseModel):
    id: int
    original_rule_id: Optional[int]
    name: str
    priority: int
    source_ip: str
    destination_ip: str
    destination_port: str
    protocol: str
    action: str
    enabled: bool
    description: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class SimulationRecordResultResponse(BaseModel):
    id: int
    record_id: str
    source_ip: str
    destination_ip: str
    destination_port: Optional[str]
    protocol: str
    decision: str
    matched_rule_id: Optional[int]
    matched_rule_name: Optional[str]
    explanation: str
    is_default_policy: bool
    validation_errors: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class SimulationSummaryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    total_records: int
    valid_records: int
    invalid_records: int
    allowed_records: int
    denied_records: int
    model_config = ConfigDict(from_attributes=True)


class PaginatedRecordResults(BaseModel):
    items: List[SimulationRecordResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SimulationDetailResponse(BaseModel):
    simulation: SimulationSummaryResponse
    rules_snapshot: List[SimulationRuleSnapshotResponse]
    records: PaginatedRecordResults


class RuleMatchStat(BaseModel):
    rule_id: Optional[int]
    rule_name: str
    match_count: int
    action: str


class DashboardStatsResponse(BaseModel):
    total_simulations: int
    total_records: int
    allowed_records: int
    allowed_percentage: float
    denied_records: int
    denied_percentage: float
    invalid_records: int
    rule_match_stats: List[RuleMatchStat]
    recent_simulations: List[SimulationSummaryResponse]
