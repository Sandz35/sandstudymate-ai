"""Tiny RAG: Titan Text Embeddings V2 + a JSON index searched with cosine similarity."""
import json
import os
from pathlib import Path

import boto3

EMBED_MODEL_ID = "amazon.titan-embed-text-v2:0"
DIMENSIONS = 256      # small vectors = small index, still good for short notes
MIN_SCORE = 0.37      # below this, a chunk is probably not about the request
MAX_CHUNK_CHARS = 1200

# In Lambda the index lives in S3; on your laptop it is a local file.
INDEX_BUCKET = os.environ.get("INDEX_BUCKET", "")
INDEX_KEY = os.environ.get("INDEX_KEY", "rag/index.json")
LOCAL_INDEX = Path(__file__).resolve().parent.parent / "knowledge" / "index.json"

_client = None
_index = None


def _bedrock():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
    return _client


def embed(text):
    """Return a normalized embedding vector for the text."""
    body = json.dumps({"inputText": text, "dimensions": DIMENSIONS, "normalize": True})
    response = _bedrock().invoke_model(
        modelId=EMBED_MODEL_ID, body=body,
        contentType="application/json", accept="application/json",
    )
    return json.loads(response["body"].read())["embedding"]


def chunk_markdown(text):
    """Split a note on '## ' headings, keeping the page title on every chunk."""
    lines = text.splitlines()
    if not lines:
        return []
    title = lines[0].lstrip("# ").strip()
    chunks, current = [], []
    for line in lines[1:]:
        if line.startswith("## ") and current:
            chunks.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    return [f"{title}\n{c}"[:MAX_CHUNK_CHARS] for c in chunks if c]


def load_index():
    """Load the index once per Lambda container (or per script run)."""
    global _index
    if _index is None:
        if INDEX_BUCKET:
            obj = boto3.client("s3").get_object(Bucket=INDEX_BUCKET, Key=INDEX_KEY)
            _index = json.loads(obj["Body"].read())
        elif LOCAL_INDEX.exists():
            _index = json.loads(LOCAL_INDEX.read_text(encoding="utf-8"))
        else:
            _index = {"chunks": []}
    return _index


def search(query_vector, chunks, k=3, subject=None):
    """Rank chunks by similarity. Vectors are normalized, so a dot product = cosine."""
    scored = []
    for chunk in chunks:
        if subject and chunk.get("subject") != subject:
            continue
        score = sum(a * b for a, b in zip(query_vector, chunk["vector"]))
        scored.append((score, chunk))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [
        {"score": round(score, 3), "id": c["id"], "source": c["source"], "text": c["text"]}
        for score, c in scored[:k]
        if score >= MIN_SCORE
    ]


def retrieve(query, subject=None, k=3):
    """Embed the query and return the top matching chunks (may be empty)."""
    chunks = load_index().get("chunks", [])
    if not chunks:
        return []
    return search(embed(query), chunks, k=k, subject=subject)
