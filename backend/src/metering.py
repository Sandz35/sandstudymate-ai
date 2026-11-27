"""Count Bedrock tokens and guardrail text units, and turn them into dollars.

wrap(client) returns a Bedrock client that records the usage of every call into
the current tally. The Lambda handler resets the tally once per request (Step 5);
the eval scripts reset it once per run.
"""
import io
import json
import time

# USD per 1M tokens (input, output). Check https://aws.amazon.com/bedrock/pricing/ and update.
TOKEN_PRICES = {
    "anthropic.claude-haiku": (1.00, 5.00),
    "amazon.nova-micro": (0.035, 0.14),
    "amazon.titan-embed-text-v2": (0.02, 0.0),
}
# USD per 1,000 guardrail text units, per policy (word filters are free).
GUARDRAIL_PRICES = {
    "contentPolicyUnits": 0.15,
    "topicPolicyUnits": 0.15,
    "sensitiveInformationPolicyUnits": 0.10,
}

_tally = None


def reset():
    """Start a new tally and return it."""
    global _tally
    _tally = {"models": {}, "guardrail_units": 0, "guardrail_ms": 0, "cost_usd": 0.0}
    return _tally


def current():
    return _tally if _tally is not None else reset()


def _short_name(model_id):
    for key in TOKEN_PRICES:
        if key in model_id:
            return key.split(".", 1)[1]  # e.g. "claude-haiku"
    return model_id


def _add_tokens(model_id, tokens_in, tokens_out, ms=0):
    tally = current()
    entry = tally["models"].setdefault(_short_name(model_id), {"calls": 0, "in": 0, "out": 0, "ms": 0})
    entry["calls"] += 1
    entry["in"] += tokens_in
    entry["out"] += tokens_out
    entry["ms"] += ms
    price_in, price_out = next((p for k, p in TOKEN_PRICES.items() if k in model_id), (0.0, 0.0))
    tally["cost_usd"] += (tokens_in * price_in + tokens_out * price_out) / 1_000_000


def _add_guardrail(usage, ms=0):
    tally = current()
    tally["guardrail_ms"] += ms
    for policy, price in GUARDRAIL_PRICES.items():
        units = usage.get(policy, 0)
        tally["guardrail_units"] += units
        tally["cost_usd"] += units * price / 1000


def _ms_since(start):
    return round((time.perf_counter() - start) * 1000)


class _MeteredBedrock:
    """Behaves like the boto3 bedrock-runtime client, but records usage."""

    def __init__(self, client):
        self._client = client

    def __getattr__(self, name):  # anything not metered passes straight through
        return getattr(self._client, name)

    def converse(self, **kwargs):
        start = time.perf_counter()
        response = self._client.converse(**kwargs)
        usage = response.get("usage", {})
        _add_tokens(kwargs.get("modelId", ""), usage.get("inputTokens", 0), usage.get("outputTokens", 0),
                    _ms_since(start))
        return response

    def invoke_model(self, **kwargs):
        start = time.perf_counter()
        response = self._client.invoke_model(**kwargs)
        raw = response["body"].read()
        _add_tokens(kwargs.get("modelId", ""), json.loads(raw).get("inputTextTokenCount", 0), 0, _ms_since(start))
        response["body"] = io.BytesIO(raw)  # the caller can still .read() it
        return response

    def apply_guardrail(self, **kwargs):
        start = time.perf_counter()
        response = self._client.apply_guardrail(**kwargs)
        _add_guardrail(response.get("usage", {}), _ms_since(start))
        return response


def wrap(client):
    return _MeteredBedrock(client)
