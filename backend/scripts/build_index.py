"""Chunk every note under backend/knowledge (any depth), embed each chunk,
write knowledge/index.json.

Layout: knowledge/<subject>/<category>/<note>.md, e.g. science/human-body/digestion.md
Run from the backend folder:  python scripts/build_index.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag import DIMENSIONS, EMBED_MODEL_ID, LOCAL_INDEX, chunk_markdown, embed  # noqa: E402

KNOWLEDGE = LOCAL_INDEX.parent
SUBJECTS = ("math", "science")

chunks = []
for path in sorted(KNOWLEDGE.rglob("*.md")):
    rel = path.relative_to(KNOWLEDGE)  # e.g. science/human-body/digestion.md
    subject = rel.parts[0]
    if subject not in SUBJECTS:
        continue
    category = rel.parts[1] if len(rel.parts) > 2 else "general"
    for i, piece in enumerate(chunk_markdown(path.read_text(encoding="utf-8"))):
        chunks.append({
            "id": f"{rel.with_suffix('').as_posix()}-{i}",  # unique even if two folders share a file name
            "source": rel.as_posix(),
            "subject": subject,
            "category": category,
            "text": piece,
            "vector": embed(piece),
        })
        print("embedded", chunks[-1]["id"])

index = {"model": EMBED_MODEL_ID, "dimensions": DIMENSIONS, "chunks": chunks}
LOCAL_INDEX.write_text(json.dumps(index), encoding="utf-8")
categories = sorted({(c["subject"], c["category"]) for c in chunks})
print(f"Wrote {len(chunks)} chunks from {len(categories)} categories to {LOCAL_INDEX}")
