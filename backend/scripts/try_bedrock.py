"""Ask Bedrock for one question and print it.

Run from the backend folder:  python scripts/try_bedrock.py math 3
"""
import json
import sys
from pathlib import Path

# Let this script import the modules in backend/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from adaptive import pick_topic  # noqa: E402
from question_gen import MODEL_ID, generate_question  # noqa: E402

subject = sys.argv[1] if len(sys.argv) > 1 else "math"
level = int(sys.argv[2]) if len(sys.argv) > 2 else 1
topic = pick_topic(subject, 0)

print(f"Model: {MODEL_ID}")
print(f"Asking for a {subject} question on '{topic}' at level {level}...")
print(json.dumps(generate_question(subject, topic, level), indent=2))

