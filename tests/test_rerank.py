"""Answerability gate (cross-encoder reranker), with a fake cross-encoder. Offline."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rag  # noqa: E402
from test_rag import PAGE1, PAGE2, index_for  # noqa: E402


class FakeCrossEncoder:
    """Scores a pair by the share of the question's long words found in the passage (0-1)."""
    def __init__(self, fail=False):
        self.fail, self.calls = fail, []

    def predict(self, pairs, show_progress_bar=False):
        if self.fail:
            raise RuntimeError("model blew up")
        self.calls.append(len(pairs))
        out = []
        for q, t in pairs:
            words = [w for w in rag.tokenize(q) if len(w) > 4]
            out.append(sum(w in t.lower() for w in words) / max(len(words), 1))
        return out


class Identity:          # named like torch.nn.Identity: scores are logits
    pass


class LogitCrossEncoder(FakeCrossEncoder):
    activation_fn = Identity()

    def predict(self, pairs, show_progress_bar=False):
        return [10.0 * (v - 0.5) for v in super().predict(pairs)]


PAGES = [(1, PAGE1), (2, PAGE2)]


def test_reranker_reorders_and_filters():
    model, index, records = index_for(PAGES)
    ce = FakeCrossEncoder()
    hits = rag.search(index, model, "preferred initial agent metformin diabetes", records,
                      min_score=0.0, reranker=ce, rerank_min=0.5)
    assert hits and hits[0]["page"] == 2 and all(h["rerank"] >= 0.5 for h in hits)
    assert ce.calls and ce.calls[0] <= rag.RERANK_CANDIDATES


def test_reranker_can_refuse_what_similarity_let_through():
    model, index, records = index_for(PAGES)
    q = "What is the enoxaparin dose for treating thrombosis?"
    plain = rag.search(index, model, q, records, min_score=0.0)
    gated = rag.search(index, model, q, records, min_score=0.0, reranker=FakeCrossEncoder(), rerank_min=0.5)
    assert plain and gated == []
    answer, cites = rag.generate_answer(q, gated)
    assert answer == rag.NOT_FOUND and cites == []


def test_failing_reranker_falls_back_to_plain_search():
    model, index, records = index_for(PAGES)
    q = "What blood pressure counts as hypertension?"
    assert rag.search(index, model, q, records, reranker=FakeCrossEncoder(fail=True)) == rag.search(index, model, q, records)


def test_logit_models_are_squashed_to_0_1():
    scores = rag.rerank_scores(LogitCrossEncoder(), "metformin diabetes preferred", [PAGE2, PAGE1])
    assert all(0.0 <= s <= 1.0 for s in scores) and scores[0] > 0.9 and scores[1] < 0.1


def test_off_means_no_reranker(monkeypatch):
    assert rag.load_reranker("off") is None
    monkeypatch.setattr(rag, "RERANKER_NAME", "off")
    assert rag.load_reranker() is None


def test_apply_rerank_top_k_and_empty():
    cands = [{"text": str(i)} for i in range(6)]
    out = rag.apply_rerank(cands, [0.1, 0.9, 0.8, 0.7, 0.6, 0.95], rerank_min=0.5, top_k=4)
    assert [c["text"] for c in out] == ["5", "1", "2", "3"]
    assert rag.apply_rerank(cands, [0.1] * 6, rerank_min=0.5) == []
    assert rag.rerank_scores(FakeCrossEncoder(), "q", []) == []


def test_eval_rerank_study_with_fake_models(monkeypatch, tmp_path):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval"))
    import run_eval
    monkeypatch.setattr(rag, "load_reranker", lambda name=None: FakeCrossEncoder())
    out = tmp_path / "r.md"
    run_eval.run(force_fake=True, out_path=str(out), quiet=True, rerankers=["fake-ce"])
    text = out.read_text()
    assert "Answerability gate" in text and "fake-ce" in text and "RERANK_MIN" in text
