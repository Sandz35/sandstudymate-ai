"""Retrieval eval: hit@1, hit@3 and MRR on the golden set, plus off-topic rejection.

Run from the backend folder:   python evals/run_retrieval.py baseline
The word after the script name labels the results file (e.g. baseline, chunker-fix).
"""
import sys

from common import cost_summary, load_cases, meter_bedrock, save_results

meter_bedrock()
from rag import MIN_SCORE, retrieve  # noqa: E402

label = sys.argv[1] if len(sys.argv) > 1 else "run"
cases = load_cases("retrieval.jsonl")
rows = []
for case in cases:
    results = retrieve(case["query"], subject=case["subject"], k=3)
    sources = [r["source"] for r in results]
    ranks = [i + 1 for i, s in enumerate(sources) if s in case["expect"]]
    rank = ranks[0] if ranks else 0
    if case["expect"]:
        ok = rank > 0
        verdict = f"HIT  rank {rank}" if ok else "MISS"
    else:
        ok = not results  # off-topic: nothing should pass the score floor
        verdict = "OK   no match" if ok else "FALSE MATCH"
    rows.append({"id": case["id"], "query": case["query"], "ok": ok, "rank": rank,
                 "top": [{"source": r["source"], "score": r["score"]} for r in results]})
    top = f"{results[0]['score']:.2f} {results[0]['source']}" if results else "-"
    print(f"{verdict:<14} {case['id']}  {case['query'][:48]:<48}  top: {top}")

positives = [r for r in rows if r["id"].startswith("r")]
negatives = [r for r in rows if not r["id"].startswith("r")]
summary = {
    "label": label,
    "min_score": MIN_SCORE,
    "cases": len(rows),
    "hit_at_1": round(sum(r["rank"] == 1 for r in positives) / len(positives), 3),
    "hit_at_3": round(sum(r["rank"] > 0 for r in positives) / len(positives), 3),
    "mrr": round(sum(1 / r["rank"] for r in positives if r["rank"]) / len(positives), 3),
    "offtopic_rejected": round(sum(r["ok"] for r in negatives) / len(negatives), 3) if negatives else None,
    **cost_summary(),
}
path = save_results(f"retrieval-{label}", summary, rows)
print(f"\nhit@1 {summary['hit_at_1']:.0%}   hit@3 {summary['hit_at_3']:.0%}   MRR {summary['mrr']:.2f}   "
      f"off-topic rejected {summary['offtopic_rejected']:.0%}   cost ${summary['cost_usd']:.5f}")
print(f"Saved {path}")
