"""Lambda entry point: routes API Gateway requests to the right function."""
import base64
import json
import logging
import time
import uuid

from adaptive import SUBJECT_TOPICS, Progress, pick_topic, update_progress
from question_gen import generate_question
from storage import get_store

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STORE = get_store()
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60  # sessions auto-delete after 7 days


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _read_body(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def start_session(data):
    subject = str(data.get("subject", "")).lower()
    if subject not in SUBJECT_TOPICS:
        return _response(400, {"error": "subject must be 'math' or 'science'"})
    name = str(data.get("name", "")).strip()[:30] or "Student"

    progress = Progress()
    item = {
        "session_id": str(uuid.uuid4()),
        "name": name,
        "subject": subject,
        **progress.to_dict(),
        "recent_questions": [],
        "expires_at": int(time.time()) + SESSION_TTL_SECONDS,
    }
    STORE.put(item)
    return _response(200, {
        "sessionId": item["session_id"],
        "name": name,
        "subject": subject,
        "progress": progress.to_dict(),
    })


def next_question(data):
    item = STORE.get(str(data.get("sessionId", "")))
    if not item:
        return _response(404, {"error": "Session not found"})

    progress = Progress.from_dict(item)
    topic = pick_topic(item["subject"], progress.total_answered)
    recent = list(item.get("recent_questions", []))

    question = None
    for attempt in range(2):  # the model occasionally breaks format: retry once
        try:
            question = generate_question(item["subject"], topic, progress.level, recent)
            break
        except ValueError as exc:
            logger.warning("Bad question on attempt %s: %s", attempt + 1, exc)
    if question is None:
        return _response(502, {"error": "Could not create a question. Please try again."})

    question_id = str(uuid.uuid4())
    item["current_question"] = {"id": question_id, "topic": topic, "level": progress.level, **question}
    item["recent_questions"] = (recent + [question["question"]])[-5:]
    STORE.put(item)

    return _response(200, {
        "questionId": question_id,
        "topic": topic,
        "level": progress.level,
        "question": question["question"],
        "choices": question["choices"],
        "hint": question["hint"],
    })


def submit_answer(data):
    item = STORE.get(str(data.get("sessionId", "")))
    if not item:
        return _response(404, {"error": "Session not found"})

    current = item.get("current_question")
    if not current or current["id"] != data.get("questionId"):
        return _response(409, {"error": "That question is not open (already answered?)"})

    choice = data.get("choiceIndex")
    if isinstance(choice, bool) or not isinstance(choice, int) or not 0 <= choice <= 3:
        return _response(400, {"error": "choiceIndex must be 0, 1, 2 or 3"})

    correct_index = int(current["answer_index"])
    progress, event = update_progress(Progress.from_dict(item), choice == correct_index)
    item.update(progress.to_dict())
    del item["current_question"]  # a question can only be answered once
    STORE.put(item)

    return _response(200, {
        "correct": choice == correct_index,
        "correctIndex": correct_index,
        "explanation": current.get("explanation", ""),
        "levelEvent": event,
        "progress": progress.to_dict(),
    })


ROUTES = {
    "POST /session": start_session,
    "POST /question": next_question,
    "POST /answer": submit_answer,
}


def handler(event, context):
    route = ROUTES.get(event.get("routeKey", ""))
    if route is None:
        return _response(404, {"error": "Unknown route"})
    try:
        data = _read_body(event)
    except (ValueError, TypeError):
        return _response(400, {"error": "Body must be valid JSON"})
    try:
        return route(data)
    except Exception:  # log the full error to CloudWatch, return a safe message
        logger.exception("Unhandled error on %s", event.get("routeKey"))
        return _response(500, {"error": "Something went wrong"})
