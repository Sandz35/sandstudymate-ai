from rag import chunk_markdown, search


def test_chunk_splits_on_headings():
    chunks = chunk_markdown("# Percent\n## A\nalpha\n## B\nbeta")
    assert len(chunks) == 2
    assert chunks[0].startswith("Percent")
    assert "beta" in chunks[1]


def test_search_ranks_and_filters():
    chunks = [
        {"id": "a", "source": "m", "subject": "math", "text": "A", "vector": [1.0, 0.0]},
        {"id": "b", "source": "s", "subject": "science", "text": "B", "vector": [0.0, 1.0]},
        {"id": "c", "source": "m", "subject": "math", "text": "C", "vector": [0.6, 0.8]},
    ]
    assert [r["id"] for r in search([1.0, 0.0], chunks, k=2)] == ["a", "c"]
    # the only science chunk scores 0, below MIN_SCORE, so nothing comes back
    assert search([1.0, 0.0], chunks, subject="science") == []
