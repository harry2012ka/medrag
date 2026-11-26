"""Held-out check: scores eval/holdout_questions.jsonl with the cutoffs FROZEN.

eval/questions.jsonl was used to pick MIN_SCORE, RERANK_HYBRID_MIN and RERANK_MIN, so its
numbers flatter the app a little. The holdout questions were written afterwards, were never
used to tune anything, and were checked for overlap with the tuning set (any question sharing
more than 60% of its words with a tuning question was dropped, except three deliberate
look-alikes that ask about a different fact). This script never sweeps: it runs the exact
settings the app ships with, once.

    python eval/run_holdout.py                       # hybrid search at the shipped MIN_SCORE
    python eval/run_holdout.py --reranker ncbi/MedCPT-Cross-Encoder   # + the shipped answer checker
    python eval/run_holdout.py --require-real --summary "$GITHUB_STEP_SUMMARY"

Do not tune anything on these results. If a cutoff changes, write a new holdout set.
"""

import argparse
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import rag  # noqa: E402
from run_eval import TYPES, build, get_model, load_questions, summarize  # noqa: E402

HOLDOUT = os.path.join(HERE, "holdout_questions.jsonl")


def score(model, index, records, questions, reranker=None):
    rows = []
    for item in questions:
        # no min_score / rerank_min passed: the app's shipped defaults are used
        hits = rag.search(index, model, item["q"], records, reranker=reranker)
        found = [(h["source"], h["page"]) for h in hits]
        target = (item.get("doc"), item.get("page"))
        rank = found.index(target) + 1 if target in found else None
        rows.append({**item, "returned": found, "rank": rank, "refused": not hits})
    return rows


def table(label, s):
    lines = [f"**{label}**", "",
             "| | value |", "|---|---|",
             f"| right page first (hit@1) | {s['hit@1']}% |",
             f"| right page in top 3 (hit@3) | {s['hit@3']}% |",
             f"| answerable questions wrongly refused | {s['false_refusal']}% |",
             f"| unanswerable questions correctly refused | {s['correct_refusal']}% |", "",
             "| type | n | hit@3 | refused |", "|---|---|---|---|"]
    for t in TYPES:
        b = s["by_type"][t]
        lines.append(f"| {t} | {b['n']} | {b['hit@3']}% | {b['refused']}% |")
    return "\n".join(lines) + "\n"


def misses(rows):
    out = []
    for r in rows:
        if r["type"] == "unanswerable" and not r["refused"]:
            out.append(f"- answered an unanswerable question: \"{r['q']}\" -> {r['returned'][:2]}")
        elif r["type"] != "unanswerable" and (r["rank"] is None or r["rank"] > 3):
            got = "refused" if r["refused"] else f"got {r['returned'][:3]}"
            out.append(f"- missed ({r['type']}): \"{r['q']}\" wanted {r['doc']} p{r['page']}, {got}")
    return out


def main():
    p = argparse.ArgumentParser(description="MedRAG held-out benchmark (frozen cutoffs)")
    p.add_argument("--reranker", default="", help="cross-encoder to run as the shipped answer checker")
    p.add_argument("--fake", action="store_true")
    p.add_argument("--require-real", action="store_true")
    p.add_argument("--out", default=os.path.join(HERE, "holdout_results.md"))
    p.add_argument("--summary", default=None)
    a = p.parse_args()

    questions = load_questions(HOLDOUT)
    model, model_name = get_model(force_fake=a.fake, require_real=a.require_real)
    index, records = build(model)

    hybrid = summarize(score(model, index, records, questions))
    md = [f"# MedRAG held-out results ({datetime.date.today().isoformat()})", "",
          f"{len(questions)} new questions, never used for tuning. Embedding model: {model_name}. "
          f"Cutoffs frozen at the shipped values: MIN_SCORE {rag.MIN_SCORE}, "
          f"RERANK_HYBRID_MIN {rag.RERANK_HYBRID_MIN}, RERANK_MIN {rag.RERANK_MIN}.", "",
          table(f"Search only (MIN_SCORE {rag.MIN_SCORE})", hybrid)]

    rr_rows = None
    if a.reranker:
        rr = rag.load_reranker(a.reranker)
        rr_rows = score(model, index, records, questions, reranker=rr)
        md.append(table(f"With the answer checker {a.reranker} (what the live app runs)", summarize(rr_rows)))
        miss = misses(rr_rows)
        md += [f"<details><summary>{len(miss)} misses with the answer checker</summary>", ""] + miss + ["", "</details>", ""]

    text = "\n".join(md)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    if a.summary:
        with open(a.summary, "a", encoding="utf-8") as f:
            f.write("\n" + text + "\n")


if __name__ == "__main__":
    main()
