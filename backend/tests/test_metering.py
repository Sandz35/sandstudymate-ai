import io
import json

import metering


class FakeBedrock:
    def converse(self, **kwargs):
        return {"usage": {"inputTokens": 1000, "outputTokens": 200}}

    def invoke_model(self, **kwargs):
        return {"body": io.BytesIO(json.dumps({"embedding": [0.1], "inputTextTokenCount": 10}).encode())}

    def apply_guardrail(self, **kwargs):
        return {"usage": {"contentPolicyUnits": 1, "topicPolicyUnits": 1, "wordPolicyUnits": 1}}


def test_costs_add_up():
    metering.reset()
    client = metering.wrap(FakeBedrock())
    client.converse(modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0")
    client.apply_guardrail(guardrailIdentifier="x")
    tally = metering.current()
    haiku = tally["models"]["claude-haiku"]
    assert (haiku["calls"], haiku["in"], haiku["out"]) == (1, 1000, 200)
    assert haiku["ms"] >= 0
    assert tally["guardrail_units"] == 2  # word filter is free, so not counted
    assert abs(tally["cost_usd"] - (0.001 + 0.001 + 0.0003)) < 1e-9


def test_embedding_body_still_readable():
    metering.reset()
    client = metering.wrap(FakeBedrock())
    response = client.invoke_model(modelId="amazon.titan-embed-text-v2:0", body="{}")
    assert json.loads(response["body"].read())["embedding"] == [0.1]
    assert metering.current()["models"]["titan-embed-text-v2"]["in"] == 10
