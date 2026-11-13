"""Lambda entry point (v2): adds POST /chat for free-text practice topics."""
import base64
import json
import logging
import time
import uuid

from adaptive import SUBJECT_TOPICS, Progress, pick_topic, update_progress
from guard import check_input
from question_gen import generate_question
from rag import retrieve
from router import understand_request
from storage import get_store

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STORE = get_store()
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGE_CHARS = 300


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


def _context_for(query, subject):
    """Retrieve note texts; on any error carry on without notes."""
    try:
        return [r["text"] for r in retrieve(query, subject=subject)]
    except Exception:
        logger.exception("Retrieval failed; continuing without notes")
        return []


def _new_question(item):
    """Create, save and return the next question. Returns (status, body)."""
    progress = Progress.from_dict(item)
    custom_topic = item.get("custom_topic")
    if custom_topic:
        topic = custom_topic
        context = list(item.get("context", []))  # retrieved once, when the topic was set
    else:
        topic = pick_topic(item["subject"], progress.total_answered)
        context = _context_for(topic, item["subject"])
    recent = list(item.get("recent_questions", []))

    question = None
    for attempt in range(2):
        try:
            question = generate_question(item["subject"], topic, progress.level, recent, context)
            break
        except ValueError as exc:
            logger.warning("Bad question on attempt %s: %s", attempt + 1, exc)
    if question is None:
        return 502, {"error": "Could not create a question. Please try again."}

    question_id = str(uuid.uuid4())
    item["current_question"] = {"id": question_id, "topic": topic, "level": progress.level, **question}
    item["recent_questions"] = (recent + [question["question"]])[-5:]
    STORE.put(item)
    return 200, {
        "questionId": question_id,
        "topic": topic,
        "level": progress.level,
        "question": question["question"],
        "choices": question["choices"],
        "hint": question["hint"],
        "grounded": bool(context),
    }


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
    status, body = _new_question(item)
    return _response(status, body)


def chat(data):
    item = STORE.get(str(data.get("sessionId", "")))
    if not item:
        return _response(404, {"error": "Session not found"})
    message = str(data.get("message", "")).strip()
    if not message:
        return _response(400, {"error": "Type what you want to practice"})
    if len(message) > MAX_MESSAGE_CHARS:
        return _response(400, {"error": f"Please keep it under {MAX_MESSAGE_CHARS} characters"})

    allowed, blocked_reply = check_input(message)
    if not allowed:
        logger.info("Guardrail blocked a chat message")  # never log the kid's text
        return _response(200, {"type": "blocked", "reply": blocked_reply})

    try:
        route = understand_request(message)
    except ValueError:
        return _response(200, {
            "type": "unclear",
            "reply": "Hmm, I didn't catch that. Try something like 'percentages' or 'the water cycle'.",
        })
    if not route["in_scope"]:
        return _response(200, {"type": "redirect", "reply": route["reply"]})

    item["subject"] = route["subject"]
    item["custom_topic"] = route["topic"]
    item["context"] = _context_for(route["search_query"], route["subject"])
    item["recent_questions"] = []
    item.pop("current_question", None)

    status, question = _new_question(item)
    if status != 200:
        return _response(status, question)
    return _response(200, {
        "type": "topic_set",
        "reply": route["reply"],
        "topic": route["topic"],
        "subject": route["subject"],
        "question": question,
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
    del item["current_question"]
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
    "POST /chat": chat,
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
    except Exception:
        logger.exception("Unhandled error on %s", event.get("routeKey"))
        return _response(500, {"error": "Something went wrong"})
