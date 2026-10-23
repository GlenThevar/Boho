"""Pydantic schemas for AI request/response validation (Stage 3)."""

from pydantic import BaseModel, Field
from typing import Optional, List


# ── Request models ──────────────────────────────────────────────────────────

class ExplainFindingRequest(BaseModel):
    finding_type: str = Field(..., description="shadowed | redundant | overly_permissive | implicit_deny")
    finding_summary: str = Field(..., max_length=2000)
    rule_details: Optional[dict] = None
    responsible_rules: Optional[List[dict]] = None
    severity: Optional[str] = None


class SuggestImprovementsRequest(BaseModel):
    rules: List[dict] = Field(..., description="Current enabled firewall rules")
    findings_summary: Optional[str] = Field(None, max_length=1000,
                                             description="Brief description of known issues")


class ExplainComparisonRequest(BaseModel):
    comparison_id: int
    before_label: str
    after_label: str
    total_records: int
    changed_records: int
    newly_allowed: int
    newly_denied: int
    summary_stats: dict


class AssistantRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    context_rules: Optional[List[dict]] = Field(None, description="Relevant firewall rules for context")
    context_findings: Optional[List[dict]] = Field(None, description="Relevant findings for context")
    context_comparison: Optional[dict] = Field(None, description="Relevant comparison summary for context")


# ── Response models ─────────────────────────────────────────────────────────

class AIExplanationResponse(BaseModel):
    success: bool
    ai_enabled: bool
    explanation: Optional[str] = None
    error: Optional[str] = None
    model_id: Optional[str] = None
    disclaimer: str = "This explanation is AI-generated and advisory only. It does not affect firewall decisions."


class AISuggestionItem(BaseModel):
    title: str
    description: str
    rationale: str
    impact: str


class AISuggestionsResponse(BaseModel):
    success: bool
    ai_enabled: bool
    suggestions: Optional[List[AISuggestionItem]] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None
    model_id: Optional[str] = None
    disclaimer: str = "These suggestions are AI-generated and advisory only. Review carefully before applying any changes."


class AIAssistantResponse(BaseModel):
    success: bool
    ai_enabled: bool
    answer: Optional[str] = None
    error: Optional[str] = None
    model_id: Optional[str] = None
    disclaimer: str = "This response is AI-generated based on your current policy context. Always verify with your deterministic engine."
