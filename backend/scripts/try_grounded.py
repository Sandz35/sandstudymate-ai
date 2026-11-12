"""Router -> RAG -> question, all from your laptop.

    python scripts/try_grounded.py 2 want to study percentage
The first argument is the level (1-5).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from question_gen import generate_question  # noqa: E402
from rag import retrieve  # noqa: E402
from router import understand_request  # noqa: E402

level = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
message = " ".join(sys.argv[2:]) or "want to study percentage"

route = understand_request(message)
print("Router:", json.dumps(route, indent=2))
if not route["in_scope"]:
    sys.exit(0)

notes = retrieve(route["search_query"], subject=route["subject"])
print(f"Retrieved {len(notes)} chunk(s):", [n["source"] for n in notes])

question = generate_question(route["subject"], route["topic"], level, [], [n["text"] for n in notes])
print(json.dumps(question, indent=2))
