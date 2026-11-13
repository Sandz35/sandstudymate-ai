import json

import app

FAKE_QUESTION = {
    "question": "What is 10% of 50?",
    "choices": ["5", "10", "15", "50"],
    "answer_index": 0,
    "explanation": "10% means divide by 10, so 50 / 10 = 5.",
    "hint": "Divide by 10.",
}
IN_SCOPE = {
    "in_scope": True, "subject": "math", "topic": "percentages",
    "search_query": "percent of a number", "reply": "Let's go!",
}


def call(route, body):
    resp = app.handler({"routeKey": route, "body": json.dumps(body)}, None)
    return resp["statusCode"], json.loads(resp["body"])


def setup(monkeypatch, route=IN_SCOPE):
    monkeypatch.setattr(app, "generate_question", lambda *a, **k: dict(FAKE_QUESTION))
    monkeypatch.setattr(app, "understand_request", lambda message: route)
    monkeypatch.setattr(app, "retrieve", lambda query, subject=None: [{"text": "Percent means out of 100."}])
    _, session = call("POST /session", {"subject": "science"})
    return session["sessionId"]


def test_chat_sets_topic_and_returns_question(monkeypatch):
    sid = setup(monkeypatch)
    status, body = call("POST /chat", {"sessionId": sid, "message": "I want to study percentage"})
    assert status == 200 and body["type"] == "topic_set"
    assert body["subject"] == "math"  # switched from science
    assert body["question"]["grounded"] is True
    assert "answer_index" not in body["question"]
    _, nxt = call("POST /question", {"sessionId": sid})  # stays on the chosen topic
    assert nxt["topic"] == "percentages"


def test_out_of_scope_is_redirected(monkeypatch):
    sid = setup(monkeypatch, {"in_scope": False, "reply": "Let's try a math topic!"})
    _, body = call("POST /chat", {"sessionId": sid, "message": "who is the best singer"})
    assert body["type"] == "redirect"


def test_guardrail_block_is_returned(monkeypatch):
    sid = setup(monkeypatch)
    monkeypatch.setattr(app, "check_input", lambda text: (False, "Let's keep to school topics."))
    _, body = call("POST /chat", {"sessionId": sid, "message": "something unsafe"})
    assert body == {"type": "blocked", "reply": "Let's keep to school topics."}


def test_long_message_rejected(monkeypatch):
    sid = setup(monkeypatch)
    status, _ = call("POST /chat", {"sessionId": sid, "message": "x" * 301})
    assert status == 400
