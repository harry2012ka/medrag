"""The held-out benchmark questions must stay valid and separate from the tuning set."""
import json
import os
import re

EVAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval")
HARD_NEGATIVES = {  # deliberate look-alikes that ask about a different fact
    "What INR range is targeted for a mechanical aortic valve?",
    "What is the edoxaban dose for atrial fibrillation?",
    "What antibiotic treats a urinary tract infection in a child with fever?",
}


def _load(name):
    with open(os.path.join(EVAL, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _words(s):
    return set(re.sub(r"[^a-z0-9 ]", "", s.lower()).split())


def test_holdout_targets_exist():
    for q in _load("holdout_questions.jsonl"):
        assert q["type"] in ("answerable", "paraphrase", "abbreviation", "unanswerable")
        if q["type"] == "unanswerable":
            assert "doc" not in q
            continue
        text = open(os.path.join(EVAL, "guidelines", q["doc"]), encoding="utf-8").read()
        assert f"=== page {q['page']} ===" in text, q


def test_holdout_does_not_overlap_tuning_set():
    tuning = [_words(q["q"]) for q in _load("questions.jsonl")]
    for q in _load("holdout_questions.jsonl"):
        if q["q"] in HARD_NEGATIVES:
            continue
        w = _words(q["q"])
        worst = max(len(w & t) / len(w | t) for t in tuning)
        assert worst <= 0.6, f"too close to a tuning question: {q['q']}"


def test_holdout_is_big_enough_and_mixed():
    qs = _load("holdout_questions.jsonl")
    assert len(qs) >= 100
    assert sum(q["type"] == "unanswerable" for q in qs) >= 25
