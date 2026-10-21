import json

import app

FAKE_QUESTION = {
    "question": "What is 2 + 3?",
    "choices": ["4", "5", "6", "7"],
    "answer_index": 1,
    "explanation": "2 + 3 = 5.",
    "hint": "Count up from 2.",
}


def call(route, body):
    resp = app.handler({"routeKey": route, "body": json.dumps(body)}, None)
    return resp["statusCode"], json.loads(resp["body"])


def use_fake_bedrock(monkeypatch):
    monkeypatch.setattr(app, "generate_question", lambda *args, **kwargs: dict(FAKE_QUESTION))


def test_full_flow_levels_up(monkeypatch):
    use_fake_bedrock(monkeypatch)
    status, session = call("POST /session", {"name": "Sandy", "subject": "math"})
    assert status == 200
    sid = session["sessionId"]

    for expected_event in ["same", "level_up"]:
        status, q = call("POST /question", {"sessionId": sid})
        assert status == 200
        assert "answer_index" not in q  # the answer never leaves the server
        status, result = call("POST /answer", {"sessionId": sid, "questionId": q["questionId"], "choiceIndex": 1})
        assert status == 200
        assert result["correct"] is True
        assert result["levelEvent"] == expected_event

    assert result["progress"]["level"] == 2


def test_bad_subject_is_rejected():
    status, body = call("POST /session", {"subject": "history"})
    assert status == 400


def test_unknown_session_is_404():
    status, body = call("POST /question", {"sessionId": "does-not-exist"})
    assert status == 404


def test_cannot_answer_twice(monkeypatch):
    use_fake_bedrock(monkeypatch)
    _, session = call("POST /session", {"subject": "science"})
    sid = session["sessionId"]
    _, q = call("POST /question", {"sessionId": sid})
    answer = {"sessionId": sid, "questionId": q["questionId"], "choiceIndex": 0}
    assert call("POST /answer", answer)[0] == 200
    assert call("POST /answer", answer)[0] == 409
