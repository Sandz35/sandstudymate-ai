"""Search the notes.  python scripts/try_retrieve.py how do I find 20 percent of 50"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag import retrieve  # noqa: E402

query = " ".join(sys.argv[1:]) or "percent of a number"
results = retrieve(query)
if not results:
    print("No chunk scored above the threshold. Add or improve a note for this topic.")
for r in results:
    print(f"{r['score']:.3f}  {r['source']}")
    print("       " + r["text"][:120].replace("\n", " "))
