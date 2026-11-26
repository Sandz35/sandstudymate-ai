"""Bedrock Guardrails checks. Skipped when GUARDRAIL_ID is not set (local unit tests)."""
import os

import boto3

GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "1")
DEFAULT_BLOCK_MESSAGE = "Let's keep to Math and Science practice! Try a topic like fractions or the water cycle."

_client = None


def _bedrock():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
    return _client


def _check(text, source):
    """Return (allowed, message_to_show_if_blocked)."""
    if not GUARDRAIL_ID:
        return True, ""
    response = _bedrock().apply_guardrail(
        guardrailIdentifier=GUARDRAIL_ID,
        guardrailVersion=GUARDRAIL_VERSION,
        source=source,
        content=[{"text": {"text": text[:2000]}}],
    )
    if response.get("action") == "GUARDRAIL_INTERVENED":
        outputs = response.get("outputs") or []
        return False, outputs[0]["text"] if outputs else DEFAULT_BLOCK_MESSAGE
    return True, ""


def check_input(text):
    return _check(text, "INPUT")


def check_output(text):
    return _check(text, "OUTPUT")
