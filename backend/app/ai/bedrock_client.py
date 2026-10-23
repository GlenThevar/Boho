"""Amazon Bedrock client for Boho Stage 3 AI features.

Reads configuration from environment variables (loaded via python-dotenv in main.py).
Never hardcodes credentials. Degrades gracefully when AI is disabled or unavailable.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# ── Configuration (read at import time after dotenv has loaded) ───────────────

def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")


def get_ai_config() -> dict:
    return {
        "enabled": _get_bool("AI_ENABLED", True),
        "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        "model_id": os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0"),
        "max_tokens": int(os.getenv("AI_MAX_TOKENS", "2048")),
        "timeout": int(os.getenv("AI_TIMEOUT_SECONDS", "30")),
    }


# ── Bedrock client ────────────────────────────────────────────────────────────

_bedrock_client = None


def _get_client():
    """Lazy-initialise boto3 Bedrock Runtime client."""
    global _bedrock_client
    if _bedrock_client is not None:
        return _bedrock_client
    try:
        import boto3
        cfg = get_ai_config()
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=cfg["region"],
        )
        return _bedrock_client
    except ImportError:
        raise RuntimeError("boto3 is not installed. Run: pip install boto3")
    except Exception as exc:
        raise RuntimeError(f"Failed to create Bedrock client: {exc}") from exc


def invoke_model(prompt: str) -> str:
    """
    Send a prompt to Amazon Bedrock and return the text response.

    Raises:
        RuntimeError: if AI is disabled, boto3 is missing, or Bedrock call fails.
    """
    cfg = get_ai_config()

    if not cfg["enabled"]:
        raise RuntimeError("AI features are disabled (AI_ENABLED=false).")

    client = _get_client()

    # Amazon Nova / Claude Messages API payload
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        "inferenceConfig": {
            "maxTokens": cfg["max_tokens"],
            "temperature": 0.3,
            "topP": 0.9,
        },
    }

    try:
        response = client.invoke_model(
            modelId=cfg["model_id"],
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json",
        )
        body = json.loads(response["body"].read())

        # Extract text — handle both Nova (output.message.content) and Claude shapes
        text = _extract_text(body)
        if not text:
            raise RuntimeError("Bedrock returned an empty response.")
        return text.strip()

    except client.exceptions.AccessDeniedException as exc:
        logger.error("Bedrock access denied: %s", exc)
        raise RuntimeError(
            "AWS access denied. Check IAM permissions for bedrock:InvokeModel."
        ) from exc
    except client.exceptions.ThrottlingException as exc:
        logger.warning("Bedrock throttled: %s", exc)
        raise RuntimeError("Bedrock request was throttled. Please try again later.") from exc
    except client.exceptions.ValidationException as exc:
        logger.error("Bedrock validation error: %s", exc)
        raise RuntimeError(f"Bedrock validation error: {exc}") from exc
    except Exception as exc:
        logger.error("Bedrock invoke_model failed: %s", exc)
        raise RuntimeError(f"Bedrock call failed: {exc}") from exc


def _extract_text(body: dict) -> str:
    """Extract text from Bedrock response body (handles Nova and Claude shapes)."""
    # Amazon Nova shape: {"output": {"message": {"content": [{"text": "..."}]}}}
    try:
        return body["output"]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    # Claude / Converse API shape: {"content": [{"text": "..."}]}
    try:
        return body["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        pass

    # Fallback: completion field
    try:
        return body["completion"]
    except (KeyError, TypeError):
        pass

    return ""
