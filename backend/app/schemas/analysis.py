from datetime import datetime
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.firewall import FirewallRuleCreate, FirewallRuleResponse


class SecurityFindingResponse(BaseModel):
    id: int
    analysis_id: int
    finding_code: str
    rule_id: Optional[int]
    rule_name: str
    rule_priority: int
    category: str
    severity: str
    finding_type: str
    title: str
    explanation: str
    evidence: Optional[Dict[str, Any]] = None
    remediation: str
    confidence: str
    is_dismissed: bool
    dismissed_reason: Optional[str]
    dismissed_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class DismissFindingRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for dismissing the security finding")


class PolicyAnalysisSummaryResponse(BaseModel):
    id: int
    created_at: datetime
    status: str
    rules_analyzed_count: int
    shadowed_count: int
    redundant_count: int
    findings_count: int
    severity_distribution: Dict[str, int] = Field(default_factory=dict)
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)


class PolicyAnalysisRuleSnapshotResponse(BaseModel):
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


class PolicyAnalysisDetailResponse(BaseModel):
    analysis: PolicyAnalysisSummaryResponse
    rules_snapshot: List[PolicyAnalysisRuleSnapshotResponse]
    findings: List[SecurityFindingResponse]


class PolicyComparisonCreateRequest(BaseModel):
    simulation_id: int
    name: Optional[str] = None
    proposed_rules: List[FirewallRuleCreate]


class PolicyComparisonSummaryResponse(BaseModel):
    id: int
    simulation_id: int
    created_at: datetime
    name: str
    original_allowed: int
    proposed_allowed: int
    original_denied: int
    proposed_denied: int
    total_records: int
    changed_decisions: int
    allow_to_deny: int
    deny_to_allow: int
    rule_changes_only: int
    model_config = ConfigDict(from_attributes=True)


class PolicyComparisonRecordResponse(BaseModel):
    id: int
    record_id: str
    source_ip: str
    destination_ip: str
    destination_port: Optional[str]
    protocol: str
    original_decision: str
    proposed_decision: str
    original_rule_id: Optional[int]
    original_rule_name: Optional[str]
    proposed_rule_id: Optional[int]
    proposed_rule_name: Optional[str]
    change_type: str
    explanation: str
    model_config = ConfigDict(from_attributes=True)


class PaginatedComparisonRecords(BaseModel):
    items: List[PolicyComparisonRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ComparisonRuleSnapshotItem(BaseModel):
    id: int
    snapshot_type: str
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


class PolicyComparisonDetailResponse(BaseModel):
    comparison: PolicyComparisonSummaryResponse
    original_rules: List[ComparisonRuleSnapshotItem]
    proposed_rules: List[ComparisonRuleSnapshotItem]
    records: PaginatedComparisonRecords
