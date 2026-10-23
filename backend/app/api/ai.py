"""AI API router for Boho Stage 3 (Amazon Bedrock integration).

All endpoints are advisory only. They never modify firewall rules or override
the deterministic engine. AI is treated as a read-only suggestion layer.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.ai.bedrock_client import invoke_model, get_ai_config
from app.ai.schemas import (
    ExplainFindingRequest,
    SuggestImprovementsRequest,
    ExplainComparisonRequest,
    AssistantRequest,
    AIExplanationResponse,
    AISuggestionsResponse,
    AISuggestionItem,
    AIAssistantResponse,
)
from app.ai.prompts import (
    build_explain_finding_prompt,
    build_suggest_improvements_prompt,
    build_explain_comparison_prompt,
    build_assistant_prompt,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Assistant (Stage 3)"])

_DISCLAIMER_EXPLANATION = (
    "This explanation is AI-generated and advisory only. "
    "It does not affect firewall decisions."
)
_DISCLAIMER_SUGGESTIONS = (
    "These suggestions are AI-generated and advisory only. "
    "Review carefully before applying any changes."
)
_DISCLAIMER_ASSISTANT = (
    "This response is AI-generated based on your current policy context. "
    "Always verify with your deterministic engine."
)


def _ai_disabled_response(model_cls, **extra):
    """Return a graceful disabled response without raising an HTTP error."""
    cfg = get_ai_config()
    return model_cls(
        success=False,
        ai_enabled=False,
        error="AI features are currently disabled.",
        model_id=cfg["model_id"],
        **extra,
    )


# ── POST /api/ai/explain-finding ─────────────────────────────────────────────

@router.post("/explain-finding", response_model=AIExplanationResponse)
def explain_finding(req: ExplainFindingRequest):
    """Explain a security finding (shadowed rule, redundant rule, overly permissive policy, etc.)."""
    cfg = get_ai_config()
    if not cfg["enabled"]:
        return _ai_disabled_response(AIExplanationResponse, disclaimer=_DISCLAIMER_EXPLANATION)

    prompt = build_explain_finding_prompt(
        finding_type=req.finding_type,
        finding_summary=req.finding_summary,
        rule_details=req.rule_details,
        responsible_rules=req.responsible_rules,
        severity=req.severity,
    )

    try:
        text = invoke_model(prompt)
        return AIExplanationResponse(
            success=True,
            ai_enabled=True,
            explanation=text,
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_EXPLANATION,
        )
    except RuntimeError as exc:
        logger.warning("explain-finding AI error: %s", exc)
        return AIExplanationResponse(
            success=False,
            ai_enabled=True,
            error=str(exc),
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_EXPLANATION,
        )


# ── POST /api/ai/suggest-improvements ────────────────────────────────────────

@router.post("/suggest-improvements", response_model=AISuggestionsResponse)
def suggest_improvements(req: SuggestImprovementsRequest):
    """Suggest safer firewall rule configurations."""
    cfg = get_ai_config()
    if not cfg["enabled"]:
        return _ai_disabled_response(AISuggestionsResponse, disclaimer=_DISCLAIMER_SUGGESTIONS)

    if not req.rules:
        raise HTTPException(status_code=400, detail="No rules provided for analysis.")

    prompt = build_suggest_improvements_prompt(
        rules=req.rules,
        findings_summary=req.findings_summary,
    )

    try:
        raw = invoke_model(prompt)
        suggestions = _parse_suggestions(raw)
        return AISuggestionsResponse(
            success=True,
            ai_enabled=True,
            suggestions=suggestions,
            raw_text=raw,
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_SUGGESTIONS,
        )
    except RuntimeError as exc:
        logger.warning("suggest-improvements AI error: %s", exc)
        return AISuggestionsResponse(
            success=False,
            ai_enabled=True,
            error=str(exc),
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_SUGGESTIONS,
        )


# ── POST /api/ai/explain-comparison ──────────────────────────────────────────

@router.post("/explain-comparison", response_model=AIExplanationResponse)
def explain_comparison(req: ExplainComparisonRequest):
    """Summarise the before/after differences in a policy comparison."""
    cfg = get_ai_config()
    if not cfg["enabled"]:
        return _ai_disabled_response(AIExplanationResponse, disclaimer=_DISCLAIMER_EXPLANATION)

    prompt = build_explain_comparison_prompt(
        before_label=req.before_label,
        after_label=req.after_label,
        total_records=req.total_records,
        changed_records=req.changed_records,
        newly_allowed=req.newly_allowed,
        newly_denied=req.newly_denied,
        summary_stats=req.summary_stats,
    )

    try:
        text = invoke_model(prompt)
        return AIExplanationResponse(
            success=True,
            ai_enabled=True,
            explanation=text,
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_EXPLANATION,
        )
    except RuntimeError as exc:
        logger.warning("explain-comparison AI error: %s", exc)
        return AIExplanationResponse(
            success=False,
            ai_enabled=True,
            error=str(exc),
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_EXPLANATION,
        )


# ── POST /api/ai/assistant ────────────────────────────────────────────────────

@router.post("/assistant", response_model=AIAssistantResponse)
def assistant(req: AssistantRequest):
    """Context-aware Q&A assistant about rules, findings, and comparisons."""
    cfg = get_ai_config()
    if not cfg["enabled"]:
        return _ai_disabled_response(AIAssistantResponse, disclaimer=_DISCLAIMER_ASSISTANT)

    # Sanitise user input — treat as untrusted
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    prompt = build_assistant_prompt(
        question=question,
        context_rules=req.context_rules,
        context_findings=req.context_findings,
        context_comparison=req.context_comparison,
    )

    try:
        text = invoke_model(prompt)
        return AIAssistantResponse(
            success=True,
            ai_enabled=True,
            answer=text,
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_ASSISTANT,
        )
    except RuntimeError as exc:
        logger.warning("assistant AI error: %s", exc)
        return AIAssistantResponse(
            success=False,
            ai_enabled=True,
            error=str(exc),
            model_id=cfg["model_id"],
            disclaimer=_DISCLAIMER_ASSISTANT,
        )


# ── GET /api/ai/status ────────────────────────────────────────────────────────

@router.get("/status")
def ai_status():
    """Return whether AI is enabled and which model is configured."""
    cfg = get_ai_config()
    return {
        "ai_enabled": cfg["enabled"],
        "model_id": cfg["model_id"],
        "region": cfg["region"],
        "max_tokens": cfg["max_tokens"],
    }


# ── Suggestion parser ─────────────────────────────────────────────────────────

def _parse_suggestions(raw: str) -> list[AISuggestionItem]:
    """Parse structured suggestions from Bedrock text output."""
    suggestions = []
    current: dict = {}

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("SUGGESTION:"):
            if current.get("title"):
                suggestions.append(_make_suggestion(current))
            current = {"title": line[len("SUGGESTION:"):].strip()}
        elif line.startswith("CHANGE:"):
            current["description"] = line[len("CHANGE:"):].strip()
        elif line.startswith("RATIONALE:"):
            current["rationale"] = line[len("RATIONALE:"):].strip()
        elif line.startswith("IMPACT:"):
            current["impact"] = line[len("IMPACT:"):].strip()

    if current.get("title"):
        suggestions.append(_make_suggestion(current))

    # If parsing yielded nothing (model used different format), wrap the whole text
    if not suggestions and raw.strip():
        suggestions.append(AISuggestionItem(
            title="AI Recommendations",
            description=raw.strip()[:500],
            rationale="See full text above.",
            impact="Review carefully before applying.",
        ))

    return suggestions[:5]  # cap at 5


def _make_suggestion(d: dict) -> AISuggestionItem:
    return AISuggestionItem(
        title=d.get("title", "Recommendation"),
        description=d.get("description", ""),
        rationale=d.get("rationale", ""),
        impact=d.get("impact", ""),
    )
