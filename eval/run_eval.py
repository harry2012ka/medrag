"""MedRAG retrieval accuracy benchmark.

Builds a search index from eval/guidelines/*.txt (synthetic documents) and runs every
question in eval/questions.jsonl through rag.search, the same search the app uses.

Reports:
  hit@1 / hit@3        the correct document + page is the 1st / in the top 3 passages shown
  correct refusal      unanswerable questions that got no passages (the user sees NOT_FOUND)
  false refusal        answerable questions that got no passages
  per-type breakdown   answerable, paraphrase, abbreviation, unanswerable

Run:
  python eval/run_eval.py                    # writes eval/results.md
  python eval/run_eval.py --threshold-sweep  # also prints the MIN_SCORE trade-off table
  python eval/run_eval.py --fake             # force the offline test model
"""

import argparse
import datetime
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import rag  # noqa: E402

ANSWERABLE_TYPES = ("answerable", "paraphrase", "abbreviation")
TYPES = ANSWERABLE_TYPES + ("unanswerable",)
SWEEP = (0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)


def load_pages(path):
    """Same '=== page N ===' format as samples/sample_guideline.txt."""
    raw = open(path, encoding="utf-8").read()
    pages = []
    for block in raw.split("=== page ")[1:]:
        number, _, text = block.partition("===")
        pages.append((int(number.strip()), " ".join(text.split())))
    return pages


def load_questions(path=os.path.join(HERE, "questions.jsonl")):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def get_model(force_fake=False):
    """(model, name). Real model if installed and loadable, else the offline test model."""
    if not force_fake:
        try:
            return rag.load_embedding_model(), rag.EMBEDDING_MODEL_NAME
        except Exception as e:
            print(f"WARNING: real embedding model unavailable ({type(e).__name__}: {e}).\n"
                  "WARNING: falling back to the offline BagOfWordsModel from tests/. These numbers "
                  "measure the pipeline logic, NOT the accuracy of the deployed app.", file=sys.stderr)
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    from test_rag import BagOfWordsModel
    return BagOfWordsModel(), "BagOfWordsModel (offline test stand-in)"


def build(model, guideline_dir=os.path.join(HERE, "guidelines")):
    records = []
    for path in sorted(glob.glob(os.path.join(guideline_dir, "*.txt"))):
        for c in rag.chunk_pages(load_pages(path)):
            records.append({"source": os.path.basename(path), "page": c["page"],
                            "chunk": len(records), "text": c["text"]})
    vecs = rag.embed_texts(model, [r["text"] for r in records])
    return rag.build_index(records, vecs), records


def evaluate(model, index, records, questions, min_score=rag.MIN_SCORE):
    rows = []
    for item in questions:
        hits = rag.search(index, model, item["q"], records, min_score=min_score)
        found = [(h["source"], h["page"]) for h in hits]
        target = (item.get("doc"), item.get("page"))
        rank = found.index(target) + 1 if target in found else None
        rows.append({**item, "returned": found, "rank": rank, "refused": not hits})
    return rows


def _pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


def summarize(rows):
    def block(rs):
        n = len(rs)
        return {"n": n,
                "hit@1": _pct(sum(r["rank"] == 1 for r in rs), n),
                "hit@3": _pct(sum(r["rank"] is not None and r["rank"] <= 3 for r in rs), n),
                "refused": _pct(sum(r["refused"] for r in rs), n)}
    ans = [r for r in rows if r["type"] in ANSWERABLE_TYPES]
    una = [r for r in rows if r["type"] == "unanswerable"]
    a = block(ans)
    return {"answerable_all": a,
            "hit@1": a["hit@1"], "hit@3": a["hit@3"],
            "false_refusal": a["refused"],
            "correct_refusal": block(una)["refused"],
            "by_type": {t: block([r for r in rows if r["type"] == t]) for t in TYPES}}


def sweep(model, index, records, questions, values=SWEEP):
    out = []
    for v in values:
        s = summarize(evaluate(model, index, records, questions, min_score=v))
        out.append((v, s["hit@1"], s["hit@3"], s["false_refusal"], s["correct_refusal"]))
    return out


def sweep_table(rows):
    lines = ["| MIN_SCORE | hit@1 | hit@3 | false refusal | correct refusal |", "|---|---|---|---|---|"]
    for v, h1, h3, fr, cr in rows:
        mark = " (current)" if abs(v - rag.MIN_SCORE) < 1e-9 else ""
        lines.append(f"| {v:.2f}{mark} | {h1}% | {h3}% | {fr}% | {cr}% |")
    return "\n".join(lines)


def report_markdown(model_name, questions, rows, s, sweep_rows=None):
    n_docs = len({q["doc"] for q in questions if q.get("doc")})
    lines = [
        "# MedRAG retrieval benchmark results", "",
        f"_Generated {datetime.date.today()} by `python eval/run_eval.py`. Embedding model: **{model_name}**. "
        f"MIN_SCORE = {rag.MIN_SCORE}, TOP_K = {rag.TOP_K}._", "",
    ]
    if "BagOfWords" in model_name:
        lines += ["> **Offline stand-in model.** These numbers come from the word-hashing test model, not "
                  f"`{rag.EMBEDDING_MODEL_NAME}`. They check the pipeline, not real-world accuracy. Re-run with "
                  "sentence-transformers installed for the numbers that match the live app.", ""]
    lines += [
        f"{len(questions)} questions over {n_docs} synthetic documents in `eval/guidelines/`.", "",
        "| Metric | Value |", "|---|---|",
        f"| hit@1 (answerable, all types) | {s['hit@1']}% |",
        f"| hit@3 (answerable, all types) | {s['hit@3']}% |",
        f"| Correct refusal (unanswerable) | {s['correct_refusal']}% |",
        f"| False refusal (answerable) | {s['false_refusal']}% |", "",
        "## By question type", "",
        "| Type | n | hit@1 | hit@3 | returned nothing |", "|---|---|---|---|---|",
    ]
    for t, b in s["by_type"].items():
        h1, h3 = ("-", "-") if t == "unanswerable" else (f"{b['hit@1']}%", f"{b['hit@3']}%")
        lines.append(f"| {t} | {b['n']} | {h1} | {h3} | {b['refused']}% |")
    if sweep_rows:
        lines += ["", "## Relevance cutoff trade-off", "", sweep_table(sweep_rows)]
    misses = [r for r in rows if (r["type"] in ANSWERABLE_TYPES and r["rank"] != 1)
              or (r["type"] == "unanswerable" and not r["refused"])]
    lines += ["", "## Misses", ""]
    if not misses:
        lines.append("None.")
    for r in misses:
        want = f"{r['doc']} p.{r['page']}" if r.get("doc") else "nothing"
        got = ", ".join(f"{d} p.{p}" for d, p in r["returned"]) or "nothing"
        lines.append(f"- [{r['type']}] {r['q']}: wanted {want}; got {got}")
    return "\n".join(lines) + "\n"


def run(force_fake=False, threshold_sweep=False, out_path=os.path.join(HERE, "results.md"), quiet=False):
    model, model_name = get_model(force_fake)
    index, records = build(model)
    questions = load_questions()
    rows = evaluate(model, index, records, questions)
    s = summarize(rows)
    sweep_rows = sweep(model, index, records, questions) if threshold_sweep else None
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_markdown(model_name, questions, rows, s, sweep_rows))
    if not quiet:
        print(f"Model: {model_name}")
        print(f"{len(questions)} questions, {len(records)} passages")
        print(f"hit@1 {s['hit@1']}%  hit@3 {s['hit@3']}%  correct refusal {s['correct_refusal']}%  "
              f"false refusal {s['false_refusal']}%")
        for t, b in s["by_type"].items():
            hits = (" " * 30) if t == "unanswerable" else f"hit@1 {b['hit@1']:5.1f}%  hit@3 {b['hit@3']:5.1f}%  "
            print(f"  {t:13s} n={b['n']:3d}  {hits}returned nothing {b['refused']:5.1f}%")
        if sweep_rows:
            print("\n" + sweep_table(sweep_rows))
        if out_path:
            print(f"\nWrote {os.path.relpath(out_path, ROOT)}")
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--threshold-sweep", action="store_true", help="try several MIN_SCORE values")
    p.add_argument("--fake", action="store_true", help="use the offline test model even if the real one is installed")
    p.add_argument("--out", default=os.path.join(HERE, "results.md"), help="where to write the markdown report")
    a = p.parse_args()
    run(force_fake=a.fake, threshold_sweep=a.threshold_sweep, out_path=a.out)


if __name__ == "__main__":
    main()
