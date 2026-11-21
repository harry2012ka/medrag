"""The accuracy benchmark runs offline with the fake model and its numbers stay sane.

Floors are deliberately loose: the word-hashing stand-in is much weaker than the real
embedding model, and this test is about the harness working, not tuning to it.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eval"))
import run_eval  # noqa: E402


def test_question_set_is_well_formed():
    qs = run_eval.load_questions()
    assert len(qs) >= 60
    docs = {os.path.basename(p) for p in os.listdir(os.path.join(ROOT, "eval", "guidelines"))}
    for q in qs:
        assert q["type"] in run_eval.TYPES, q
        if q["type"] == "unanswerable":
            assert q["doc"] is None and q["page"] is None, q
        else:
            assert q["doc"] in docs and isinstance(q["page"], int), q
    for t in run_eval.TYPES:
        assert sum(q["type"] == t for q in qs) >= 10, t


def test_eval_runs_with_fake_model(tmp_path):
    out = tmp_path / "results.md"
    s = run_eval.run(force_fake=True, threshold_sweep=True, out_path=str(out), quiet=True)
    assert s["correct_refusal"] >= 70.0          # off-topic questions get "not in your documents"
    assert s["hit@3"] >= 30.0                    # the harness finds the right page for plenty of questions
    assert s["false_refusal"] <= 60.0
    text = out.read_text()
    assert "hit@1" in text and "Offline stand-in model" in text and "MIN_SCORE" in text
    json.dumps(s)                                # summary is plain data
