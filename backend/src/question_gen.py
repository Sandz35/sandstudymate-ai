"""Ask Amazon Bedrock to write one multiple-choice question, then validate it."""
import json
import os

import boto3

from adaptive import LEVEL_DESCRIPTIONS

# Override with an environment variable if your console shows a newer model ID.
MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)

SYSTEM_PROMPT = """You are SandStudyMate, a friendly tutor for a 5th grade student (age 10-11).
Write ONE multiple-choice practice question.
Rules:
- Kind, encouraging, age-appropriate language. No trick questions.
- Exactly 4 answer choices and exactly one correct answer.
- The question is under 60 words.
- The explanation teaches the idea in 1-3 short sentences.
- The hint nudges without giving the answer away.
Reply with ONLY a JSON object, no other text, in this exact shape:
{"question": "...", "choices": ["...", "...", "...", "..."], "answer_index": 0, "explanation": "...", "hint": "..."}
answer_index is the position (0-3) of the correct choice."""

_client = None


def _bedrock():
    """Create the Bedrock client once and reuse it (faster on warm Lambdas)."""
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
    return _client


def generate_question(subject, topic, level, recent_questions=None):
    """Return a dict: question, choices, answer_index, explanation, hint."""
    prompt = (
        f"Subject: {subject}\n"
        f"Topic: {topic}\n"
        f"Difficulty: level {level} of 5 ({LEVEL_DESCRIPTIONS[level]})\n"
    )
    if recent_questions:
        prompt += "Do not repeat any of these recent questions:\n"
        prompt += "\n".join(f"- {q}" for q in recent_questions[-5:])

    response = _bedrock().converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 600, "temperature": 0.8},
    )
    text = response["output"]["message"]["content"][0]["text"]
    return parse_question(text)


def parse_question(text):
    """Pull the JSON object out of the model's reply and check it is usable."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model reply contained no JSON object")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model reply was not valid JSON: {exc}") from exc

    question = str(data.get("question", "")).strip()
    choices = data.get("choices")
    answer_index = data.get("answer_index")

    if not question:
        raise ValueError("Missing question text")
    if not isinstance(choices, list) or len(choices) != 4:
        raise ValueError("Expected exactly 4 choices")
    if not isinstance(answer_index, int) or not 0 <= answer_index <= 3:
        raise ValueError("answer_index must be 0, 1, 2 or 3")

    return {
        "question": question,
        "choices": [str(c) for c in choices],
        "answer_index": answer_index,
        "explanation": str(data.get("explanation", "")),
        "hint": str(data.get("hint", "")),
    }

