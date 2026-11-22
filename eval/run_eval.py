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
  python eval/run_eval.py --require-real     # fail instead of falling back to the test model (CI)
  python eval/run_eval.py --summary FILE     # append a short markdown summary (e.g. $GITHUB_STEP_SUMMARY)
  python eval/run_eval.py --rerankers cross-encoder/ms-marco-MiniLM-L-6-v2,...
                                             # also sweep RERANK_MIN for each cross-encoder, with latency
"""

import argparse
import datetime
import glob
import json
import os
import resource
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import rag  # noqa: E402

ANSWERABLE_TYPES = ("answerable", "paraphrase", "abbreviation")
TYPES = ANSWERABLE_TYPES + ("unanswerable",)
SWEEP = (0.15, 0.20, 0.25, 0.30, 0.35, 0.38, 0.40, 0.42, 0.45, 0.50)


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


def get_model(force_fake=False, require_real=False):
    """(model, name). Real model if installed and loadable, else the offline test model."""
    if not force_fake:
        try:
            return rag.load_embedding_model(), rag.EMBEDDING_MODEL_NAME
        except Exception as e:
            if require_real:
                raise SystemExit(f"--require-real: embedding model unavailable ({type(e).__name__}: {e})")
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


FLOOR_SWEEP = (0.40, 0.42, 0.45, 0.48, 0.50)
RERANK_SWEEP = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9)
RERANK_CUTOFFS = (0.20, 0.30)
# adoption bar for the answerability gate
BAR = {"correct_refusal": 70.0, "false_refusal": 5.0, "hit@3": 85.0}


def evaluate(model, index, records, questions, min_score=rag.MIN_SCORE, floor=None):
    """floor: if set, also refuse when the best passage's similarity is under it (experiment only)."""
    rows = []
    for item in questions:
        hits = rag.search(index, model, item["q"], records, min_score=min_score)
        best = max((h["similarity"] for h in hits), default=None)
        if floor is not None and hits and best < floor:
            hits = []
        found = [(h["source"], h["page"]) for h in hits]
        target = (item.get("doc"), item.get("page"))
        rank = found.index(target) + 1 if target in found else None
        rows.append({**item, "returned": found, "rank": rank, "refused": not hits, "best": best})
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


def floor_sweep(model, index, records, questions, cutoffs=(0.30, 0.35, 0.38, 0.40), floors=FLOOR_SWEEP):
    """Inclusion cutoff x confidence floor (best passage similarity needed to answer at all)."""
    out = []
    for c in cutoffs:
        for fl in floors:
            if fl <= c:
                continue
            s = summarize(evaluate(model, index, records, questions, min_score=c, floor=fl))
            out.append((c, fl, s["hit@1"], s["hit@3"], s["false_refusal"], s["correct_refusal"]))
    return out


def floor_table(rows):
    lines = ["| MIN_SCORE | floor | hit@1 | hit@3 | false refusal | correct refusal |",
             "|---|---|---|---|---|---|"]
    for c, fl, h1, h3, fr, cr in rows:
        lines.append(f"| {c:.2f} | {fl:.2f} | {h1}% | {h3}% | {fr}% | {cr}% |")
    return "\n".join(lines)


def _rows_from(questions, hits_per_q):
    rows = []
    for item, hits in zip(questions, hits_per_q):
        found = [(h["source"], h["page"]) for h in hits]
        target = (item.get("doc"), item.get("page"))
        rank = found.index(target) + 1 if target in found else None
        rows.append({**item, "returned": found, "rank": rank, "refused": not hits,
                     "best": max((h.get("rerank", h["similarity"]) for h in hits), default=None)})
    return rows


def _latency(fn, questions):
    times = []
    for item in questions:
        t = time.perf_counter()
        fn(item["q"])
        times.append(time.perf_counter() - t)
    times.sort()
    return {"mean_ms": round(1000 * statistics.mean(times)), "p95_ms": round(1000 * times[int(0.95 * (len(times) - 1))]),
            "max_ms": round(1000 * times[-1])}


def rerank_study(model, index, records, questions, name):
    """Sweep RERANK_MIN for one cross-encoder. Scores each question's candidates once, then
    applies every threshold with rag.apply_rerank (the same code rag.search uses)."""
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    t = time.perf_counter()
    try:
        ce = rag.load_reranker(name)
    except Exception as e:
        return {"name": name, "error": f"{type(e).__name__}: {e}"}
    load_s = round(time.perf_counter() - t, 1)
    rss_mb = round((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - rss0) / 1024)
    try:
        params_m = round(sum(p.numel() for p in ce.model.parameters()) / 1e6, 1)
    except Exception:
        params_m = None
    sweep_rows, best = [], None
    for c in RERANK_CUTOFFS:
        scored = []
        for item in questions:
            cands = rag.search(index, model, item["q"], records, top_k=rag.RERANK_CANDIDATES,
                               min_score=c, max_gap=float("inf"))
            scored.append((cands, rag.rerank_scores(ce, item["q"], [x["text"] for x in cands])))
        for th in RERANK_SWEEP:
            rows = _rows_from(questions, [rag.apply_rerank(cd, sc, th, rag.TOP_K) for cd, sc in scored])
            s = summarize(rows)
            ok = (s["correct_refusal"] >= BAR["correct_refusal"] and s["false_refusal"] <= BAR["false_refusal"]
                  and s["hit@3"] >= BAR["hit@3"])
            sweep_rows.append((c, th, s["hit@1"], s["hit@3"], s["false_refusal"], s["correct_refusal"], ok))
            key = (ok, s["correct_refusal"] - 2 * s["false_refusal"], s["hit@3"])
            if best is None or key > best[0]:
                best = (key, c, th, rows)
    _, bc, bth, brows = best
    lat = _latency(lambda q: rag.search(index, model, q, records, min_score=bc, reranker=ce, rerank_min=bth), questions)
    lat1 = None
    try:
        import torch
        n = torch.get_num_threads()
        torch.set_num_threads(1)
        lat1 = _latency(lambda q: rag.search(index, model, q, records, min_score=bc, reranker=ce, rerank_min=bth),
                        questions)
        torch.set_num_threads(n)
    except Exception:
        pass
    return {"name": name, "load_s": load_s, "rss_mb": rss_mb, "params_m": params_m,
            "activation": type(next((a for a in (getattr(ce, k, None) for k in
                                                 ("activation_fn", "activation_fct", "default_activation_function"))
                                     if a is not None), None)).__name__,
            "sweep": sweep_rows, "best": (bc, bth), "best_rows": brows, "latency": lat, "latency_1thread": lat1}


def rerank_markdown(studies, baseline_latency, heading="##"):
    lines = ["", f"{heading} Answerability gate (cross-encoder reranker)", "",
             f"Top {rag.RERANK_CANDIDATES} hybrid passages (at the given MIN_SCORE) are re-scored by the "
             "cross-encoder; passages under RERANK_MIN are dropped. Adoption bar: correct refusal >= "
             f"{BAR['correct_refusal']}%, false refusal <= {BAR['false_refusal']}%, hit@3 >= {BAR['hit@3']}%.", "",
             f"Plain hybrid search latency: mean {baseline_latency['mean_ms']} ms, p95 {baseline_latency['p95_ms']} ms "
             "per question (GitHub Actions CPU).", ""]
    for st in studies:
        if "error" in st:
            lines += [f"**{st['name']}**: could not load ({st['error']}).", ""]
            continue
        bc, bth = st["best"]
        l1 = st["latency_1thread"]
        lines += [f"**{st['name']}** ({st['params_m']}M parameters, load {st['load_s']} s, about +{st['rss_mb']} MB "
                  f"peak memory, activation {st['activation']}). Latency at MIN_SCORE {bc:.2f}, RERANK_MIN {bth}: "
                  f"mean {st['latency']['mean_ms']} ms, p95 {st['latency']['p95_ms']} ms, max {st['latency']['max_ms']} ms"
                  + (f"; single CPU thread mean {l1['mean_ms']} ms, p95 {l1['p95_ms']} ms." if l1 else "."), "",
                  "| MIN_SCORE | RERANK_MIN | hit@1 | hit@3 | false refusal | correct refusal | meets bar |",
                  "|---|---|---|---|---|---|---|"]
        for c, th, h1, h3, fr, cr, ok in st["sweep"]:
            mark = " **(best)**" if (c, th) == (bc, bth) else ""
            lines.append(f"| {c:.2f} | {th}{mark} | {h1}% | {h3}% | {fr}% | {cr}% | {'yes' if ok else 'no'} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def sweep_table(rows):
    lines = ["| MIN_SCORE | hit@1 | hit@3 | false refusal | correct refusal |", "|---|---|---|---|---|"]
    for v, h1, h3, fr, cr in rows:
        mark = " (current)" if abs(v - rag.MIN_SCORE) < 1e-9 else ""
        lines.append(f"| {v:.2f}{mark} | {h1}% | {h3}% | {fr}% | {cr}% |")
    return "\n".join(lines)


def report_markdown(model_name, questions, rows, s, sweep_rows=None, floor_rows=None):
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
    if floor_rows:
        lines += ["", "## Confidence floor experiment", "",
                  "Same search, but refuse when the best passage's similarity is under the floor.", "",
                  floor_table(floor_rows)]
    misses = [r for r in rows if (r["type"] in ANSWERABLE_TYPES and r["rank"] != 1)
              or (r["type"] == "unanswerable" and not r["refused"])]
    lines += ["", "## Misses", ""]
    if not misses:
        lines.append("None.")
    for r in misses:
        want = f"{r['doc']} p.{r['page']}" if r.get("doc") else "nothing"
        got = ", ".join(f"{d} p.{p}" for d, p in r["returned"]) or "nothing"
        best = f" (best similarity {r['best']:.2f})" if r.get("best") is not None else ""
        lines.append(f"- [{r['type']}] {r['q']}: wanted {want}; got {got}{best}")
    return "\n".join(lines) + "\n"


def summary_markdown(model_name, questions, s, sweep_rows=None, floor_rows=None):
    """Short report for a CI job summary: headline metrics, per-type table, cutoff sweep."""
    lines = [f"### MedRAG retrieval benchmark ({model_name})", "",
             f"{len(questions)} questions, MIN_SCORE = {rag.MIN_SCORE}, TOP_K = {rag.TOP_K}", "",
             "| hit@1 | hit@3 | correct refusal | false refusal |", "|---|---|---|---|",
             f"| {s['hit@1']}% | {s['hit@3']}% | {s['correct_refusal']}% | {s['false_refusal']}% |", "",
             "| Type | n | hit@1 | hit@3 | returned nothing |", "|---|---|---|---|---|"]
    for t, b in s["by_type"].items():
        h1, h3 = ("-", "-") if t == "unanswerable" else (f"{b['hit@1']}%", f"{b['hit@3']}%")
        lines.append(f"| {t} | {b['n']} | {h1} | {h3} | {b['refused']}% |")
    if sweep_rows:
        lines += ["", "#### Relevance cutoff trade-off", "", sweep_table(sweep_rows)]
    if floor_rows:
        lines += ["", "#### Confidence floor experiment", "", floor_table(floor_rows)]
    return "\n".join(lines) + "\n"


def run(force_fake=False, threshold_sweep=False, out_path=os.path.join(HERE, "results.md"), quiet=False,
        require_real=False, summary_path=None, rerankers=()):
    model, model_name = get_model(force_fake, require_real)
    index, records = build(model)
    questions = load_questions()
    rows = evaluate(model, index, records, questions)
    s = summarize(rows)
    sweep_rows = sweep(model, index, records, questions) if threshold_sweep else None
    floor_rows = floor_sweep(model, index, records, questions) if threshold_sweep else None
    rr_md = ""
    if rerankers:
        base_lat = _latency(lambda q: rag.search(index, model, q, records), questions)
        studies = [rerank_study(model, index, records, questions, n) for n in rerankers]
        rr_md = rerank_markdown(studies, base_lat)
        for st in studies:
            if "best_rows" in st:
                bc, bth = st["best"]
                miss = [r for r in st["best_rows"] if (r["type"] in ANSWERABLE_TYPES and (r["rank"] or 9) > 3)
                        or (r["type"] == "unanswerable" and not r["refused"])]
                rr_md += (f"\n<details><summary>{st['name']} misses at MIN_SCORE {bc:.2f}, RERANK_MIN {bth} "
                          f"({len(miss)})</summary>\n\n" + "\n".join(
                              f"- [{r['type']}] {r['q']}: wanted "
                              + (f"{r['doc']} p.{r['page']}" if r.get('doc') else "nothing") + "; got "
                              + (", ".join(f"{d} p.{p}" for d, p in r["returned"]) or "nothing")
                              + (f" (rerank {r['best']:.3f})" if r.get("best") is not None else "")
                              for r in miss) + "\n\n</details>\n")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_markdown(model_name, questions, rows, s, sweep_rows, floor_rows) + rr_md)
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(summary_markdown(model_name, questions, s, sweep_rows, floor_rows)
                    + (rr_md.split("\n<details>")[0].replace("\n## ", "\n#### ") if rr_md else ""))
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
            print("\n" + floor_table(floor_rows))
        if rr_md:
            print(rr_md)
        if out_path:
            print(f"\nWrote {os.path.relpath(out_path, ROOT)}")
    return s


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--threshold-sweep", action="store_true", help="try several MIN_SCORE values")
    p.add_argument("--fake", action="store_true", help="use the offline test model even if the real one is installed")
    p.add_argument("--out", default=os.path.join(HERE, "results.md"), help="where to write the markdown report")
    p.add_argument("--require-real", action="store_true", help="exit with an error if the real model can't load")
    p.add_argument("--summary", default=None, help="append a short markdown summary to this file")
    p.add_argument("--rerankers", default="", help="comma-separated cross-encoder names to evaluate")
    a = p.parse_args()
    run(force_fake=a.fake, threshold_sweep=a.threshold_sweep, out_path=a.out,
        require_real=a.require_real, summary_path=a.summary,
        rerankers=[n.strip() for n in a.rerankers.split(",") if n.strip()])


if __name__ == "__main__":
    main()
