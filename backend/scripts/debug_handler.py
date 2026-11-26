"""Run the Lambda handler on your laptop, one route at a time, so you can step through it.

Put this file in backend/scripts/ and run it under the VS Code debugger
(launch.json config "Debug backend flow"), or plainly:
    cd backend
    python scripts/debug_handler.py

It calls app.handler() exactly the way API Gateway does in AWS, with the same
event shape. Bedrock calls are REAL (small cost, same as try_grounded.py).
Storage is in-memory unless TABLE_NAME is set, so nothing touches DynamoDB.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import app  # noqa: E402  (the same module Lambda loads)


def call(route, body):
    """Build the event API Gateway would send, call the handler, print the result."""
    event = {"routeKey": route, "body": json.dumps(body)}
    resp = app.handler(event, None)  # <- set a breakpoint here, then F11 to step in
    data = json.loads(resp["body"])
    print(f"\n=== {route} -> {resp['statusCode']}")
    print(json.dumps(data, indent=2))
    return data


# 1. POST /session
session = call("POST /session", {"name": "Sandy", "subject": "math"})
sid = session["sessionId"]

# 2. POST /question  (router-free path: pick_topic -> retrieve -> generate)
question = call("POST /question", {"sessionId": sid})

# Peek at what the browser never sees: the stored answer
stored = app.STORE.get(sid)["current_question"]
print(f"\n(hidden on server) answer_index = {stored['answer_index']}")

# 3. POST /answer  (answer correctly)
call("POST /answer", {
    "sessionId": sid,
    "questionId": question["questionId"],
    "choiceIndex": int(stored["answer_index"]),
})

# 4. Replay the same answer -> expect 409
call("POST /answer", {
    "sessionId": sid,
    "questionId": question["questionId"],
    "choiceIndex": 0,
})

# 5. POST /chat  (guardrail -> router -> retrieve -> generate)
call("POST /chat", {"sessionId": sid, "message": "I want to study percentages"})

# 6. POST /chat off-topic -> expect type "redirect"
call("POST /chat", {"sessionId": sid, "message": "who is the most famous singer"})