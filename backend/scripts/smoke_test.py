"""Call the live API end to end.

Run from the backend folder:
    python scripts/smoke_test.py https://abc123.execute-api.us-east-1.amazonaws.com
"""
import json
import sys
import urllib.error
import urllib.request


def post(base_url, path, body):
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.loads(response.read())


def main():
    base = sys.argv[1]
    session = post(base, "/session", {"name": "Tester", "subject": "math"})
    print("Session:", json.dumps(session, indent=2))

    question = post(base, "/question", {"sessionId": session["sessionId"]})
    print("Question:", json.dumps(question, indent=2))

    result = post(base, "/answer", {
        "sessionId": session["sessionId"],
        "questionId": question["questionId"],
        "choiceIndex": 0,
    })
    print("Answer result:", json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as err:
        print("HTTP", err.code, err.read().decode())
        sys.exit(1)
