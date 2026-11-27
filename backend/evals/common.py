"""Shared helpers for the offline evals. Run every eval from the backend folder."""
import json
import os
import re
import sys
import time
from pathlib import Path

EVALS = Path(__file__).resolve().parent
BACKEND = EVALS.parent
sys.path.insert(0, str(BACKEND / "src"))


def _use_deployed_settings():
    """Copy the model IDs and guardrail from samconfig.toml, so evals test what is deployed."""
    config = (BACKEND / "samconfig.toml").read_text(encoding="utf-8")
    wanted = {
        "BedrockModelId": "BEDROCK_MODEL_ID",
        "RouterModelId": "ROUTER_MODEL_ID",
        "GuardrailId": "GUARDRAIL_ID",
        "GuardrailVersion": "GUARDRAIL_VERSION",
    }
    for param, env_name in wanted.items():
        match = re.search(param + r'=\\"([^\\"]*)\\"', config)
        if match:
            os.environ.setdefault(env_name, match.group(1))
    region = re.search(r'region\s*=\s*"([^"]+)"', config)
    os.environ.setdefault("AWS_DEFAULT_REGION", region.group(1) if region else "us-east-2")


_use_deployed_settings()  # must run before the app modules are imported

import boto3  # noqa: E402

import metering  # noqa: E402


def meter_bedrock():
    """Send every Bedrock call from the app modules through the usage meter. Returns the client."""
    import guard
    import question_gen
    import rag
    import router

    client = metering.wrap(boto3.client("bedrock-runtime"))
    for module in (guard, question_gen, rag, router):
        module._client = client
    metering.reset()
    return client


def load_cases(filename):
    """Read a .jsonl file: one JSON object per line; blank lines and # comments are skipped."""
    lines = (EVALS / filename).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip() and not line.lstrip().startswith("#")]


def save_results(name, summary, rows):
    """Write a dated results file to evals/results/ and return its path."""
    out_dir = EVALS / "results"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{time.strftime('%Y%m%d-%H%M')}-{name}.json"
    path.write_text(json.dumps({"summary": summary, "cases": rows}, indent=2), encoding="utf-8")
    return path


def cost_summary():
    tally = metering.current()
    return {"cost_usd": round(tally["cost_usd"], 5), "models": tally["models"],
            "guardrail_units": tally["guardrail_units"]}
