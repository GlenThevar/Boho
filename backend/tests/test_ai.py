"""Tests for Stage 3 AI endpoints — uses mocked boto3 to avoid real AWS calls."""

import json
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_bedrock_response(text: str) -> dict:
    """Build a fake Bedrock response shaped like Amazon Nova Pro."""
    body_bytes = json.dumps({
        "output": {
            "message": {
                "content": [{"text": text}]
            }
        }
    }).encode()
    mock_response = MagicMock()
    mock_response.__getitem__ = lambda self, key: (
        MagicMock(read=lambda: body_bytes) if key == "body" else None
    )
    return mock_response


def _bedrock_response_obj(text: str):
    body_str = json.dumps({
        "output": {
            "message": {
                "content": [{"text": text}]
            }
        }
    })

    class FakeStream:
        def read(self):
            return body_str.encode()

    class FakeResp(dict):
        pass

    resp = FakeResp()
    resp["body"] = FakeStream()
    return resp


def _get_client():
    """Lazily import TestClient to ensure dotenv is loaded first."""
    os.environ.setdefault("AI_ENABLED", "true")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    os.environ.setdefault("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "FAKE")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "FAKE")

    from app.main import app
    return TestClient(app)


# ── GET /api/ai/status ────────────────────────────────────────────────────────

def test_ai_status_enabled():
    os.environ["AI_ENABLED"] = "true"
    client = _get_client()
    resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_enabled"] is True
    assert "model_id" in data


def test_ai_status_disabled():
    os.environ["AI_ENABLED"] = "false"
    # Reset module-level cache
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()
    resp = client.get("/api/ai/status")
    assert resp.status_code == 200
    assert resp.json()["ai_enabled"] is False
    os.environ["AI_ENABLED"] = "true"


# ── POST /api/ai/explain-finding ──────────────────────────────────────────────

def test_explain_finding_success():
    client = _get_client()
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None

    fake_text = "**Issue** This rule is shadowed.\n**Remediation** Remove the earlier wildcard rule."

    with patch("boto3.client") as mock_boto3:
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = _bedrock_response_obj(fake_text)
        # Make exceptions accessible
        fake_client.exceptions.AccessDeniedException = Exception
        fake_client.exceptions.ThrottlingException = Exception
        fake_client.exceptions.ValidationException = Exception
        mock_boto3.return_value = fake_client

        bc._bedrock_client = None
        resp = client.post("/api/ai/explain-finding", json={
            "finding_type": "shadowed",
            "finding_summary": "Rule 2 is fully shadowed by Rule 1.",
            "severity": "High",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["ai_enabled"] is True
    assert fake_text in data["explanation"]
    assert "advisory" in data["disclaimer"].lower()


def test_explain_finding_ai_disabled():
    os.environ["AI_ENABLED"] = "false"
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()

    resp = client.post("/api/ai/explain-finding", json={
        "finding_type": "shadowed",
        "finding_summary": "Some finding.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["ai_enabled"] is False
    assert data["error"] is not None
    os.environ["AI_ENABLED"] = "true"


def test_explain_finding_bedrock_error():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()

    with patch("boto3.client") as mock_boto3:
        fake_client = MagicMock()
        fake_client.invoke_model.side_effect = Exception("Network timeout")
        fake_client.exceptions.AccessDeniedException = type("AccessDeniedException", (Exception,), {})
        fake_client.exceptions.ThrottlingException = type("ThrottlingException", (Exception,), {})
        fake_client.exceptions.ValidationException = type("ValidationException", (Exception,), {})
        mock_boto3.return_value = fake_client
        bc._bedrock_client = None

        resp = client.post("/api/ai/explain-finding", json={
            "finding_type": "redundant",
            "finding_summary": "Rule is redundant.",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"] is not None


# ── POST /api/ai/suggest-improvements ────────────────────────────────────────

def test_suggest_improvements_success():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()

    suggestion_text = (
        "SUGGESTION: Restrict ICMP\n"
        "CHANGE: Change ICMP ANY to ICMP from trusted subnets only.\n"
        "RATIONALE: Unrestricted ICMP can enable reconnaissance.\n"
        "IMPACT: Blocks ICMP from untrusted sources.\n"
    )

    with patch("boto3.client") as mock_boto3:
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = _bedrock_response_obj(suggestion_text)
        fake_client.exceptions.AccessDeniedException = Exception
        fake_client.exceptions.ThrottlingException = Exception
        fake_client.exceptions.ValidationException = Exception
        mock_boto3.return_value = fake_client
        bc._bedrock_client = None

        resp = client.post("/api/ai/suggest-improvements", json={
            "rules": [
                {
                    "priority": 1,
                    "name": "Allow HTTPS",
                    "source_ip": "ANY",
                    "destination_ip": "ANY",
                    "destination_port": "443",
                    "protocol": "TCP",
                    "action": "ALLOW",
                    "enabled": True,
                }
            ]
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["suggestions"] is not None
    assert len(data["suggestions"]) >= 1
    assert data["suggestions"][0]["title"] == "Restrict ICMP"


def test_suggest_improvements_empty_rules():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()
    resp = client.post("/api/ai/suggest-improvements", json={"rules": []})
    assert resp.status_code == 400


# ── POST /api/ai/explain-comparison ──────────────────────────────────────────

def test_explain_comparison_success():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()

    cmp_text = "**Overview** The new policy is more restrictive."

    with patch("boto3.client") as mock_boto3:
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = _bedrock_response_obj(cmp_text)
        fake_client.exceptions.AccessDeniedException = Exception
        fake_client.exceptions.ThrottlingException = Exception
        fake_client.exceptions.ValidationException = Exception
        mock_boto3.return_value = fake_client
        bc._bedrock_client = None

        resp = client.post("/api/ai/explain-comparison", json={
            "comparison_id": 1,
            "before_label": "Original Policy",
            "after_label": "Proposed Policy",
            "total_records": 100,
            "changed_records": 15,
            "newly_allowed": 5,
            "newly_denied": 10,
            "summary_stats": {
                "original_allowed": 60,
                "original_denied": 40,
                "proposed_allowed": 55,
                "proposed_denied": 45,
            },
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert cmp_text in data["explanation"]


# ── POST /api/ai/assistant ────────────────────────────────────────────────────

def test_assistant_success():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()

    answer_text = "You have 3 shadowed rules. Rule 2 is shadowed by Rule 1."

    with patch("boto3.client") as mock_boto3:
        fake_client = MagicMock()
        fake_client.invoke_model.return_value = _bedrock_response_obj(answer_text)
        fake_client.exceptions.AccessDeniedException = Exception
        fake_client.exceptions.ThrottlingException = Exception
        fake_client.exceptions.ValidationException = Exception
        mock_boto3.return_value = fake_client
        bc._bedrock_client = None

        resp = client.post("/api/ai/assistant", json={
            "question": "How many shadowed rules do I have?",
            "context_rules": [{"priority": 1, "name": "Block All", "action": "DENY"}],
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert answer_text in data["answer"]


def test_assistant_empty_question():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()
    resp = client.post("/api/ai/assistant", json={"question": "   "})
    assert resp.status_code == 400


def test_assistant_aws_access_denied():
    import app.ai.bedrock_client as bc
    bc._bedrock_client = None
    client = _get_client()

    AccessDeniedException = type("AccessDeniedException", (Exception,), {})

    with patch("boto3.client") as mock_boto3:
        fake_client = MagicMock()
        fake_client.invoke_model.side_effect = AccessDeniedException("Access denied")
        fake_client.exceptions.AccessDeniedException = AccessDeniedException
        fake_client.exceptions.ThrottlingException = type("ThrottlingException", (Exception,), {})
        fake_client.exceptions.ValidationException = type("ValidationException", (Exception,), {})
        mock_boto3.return_value = fake_client
        bc._bedrock_client = None

        resp = client.post("/api/ai/assistant", json={
            "question": "What are my rules?",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"] is not None


# ── Regression: Stage 1 & 2 still work ───────────────────────────────────────

def test_health_check_regression():
    client = _get_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_rules_endpoint_regression():
    client = _get_client()
    resp = client.get("/api/rules")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
