"""Offline tests for MedRAG's core (no model download, no network).

A tiny bag-of-words "embedding model" stands in for sentence-transformers, so these
tests check the pipeline logic: page extraction, chunking, relevance cutoff,
citations, and answer handling.
"""

import io
import os
import re
import sys
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rag  # noqa: E402

VOCAB_SIZE = 512


class BagOfWordsModel:
    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        out = np.zeros((len(texts), VOCAB_SIZE), dtype="float32")
        for i, t in enumerate(texts):
            for w in re.findall(r"[a-z0-9]+", t.lower()):
                if len(w) > 3:
                    out[i, hash(w) % VOCAB_SIZE] += 1
        return out


def make_pdf(pages):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for text in pages:
        y = 740
        for line in re.findall(r".{1,90}(?:\s|$)", text):
            c.drawString(40, y, line.strip())
            y -= 14
        c.showPage()
    c.save()
    return buf.getvalue()


PAGE1 = ("Hypertension is defined as a blood pressure of 130/80 mmHg or higher. "
         "Lifestyle modification is the first-line intervention for all patients.")
PAGE2 = ("Metformin remains the preferred initial pharmacologic agent for type 2 diabetes. "
         "Consider an SGLT2 inhibitor for patients with chronic kidney disease.")


def index_for(pages, name="guide.pdf"):
    model = BagOfWordsModel()
    chunks = rag.chunk_pages(pages)
    vecs = rag.embed_texts(model, [c["text"] for c in chunks])
    records = [{"source": name, "page": c["page"], "chunk": i, "text": c["text"]} for i, c in enumerate(chunks)]
    return model, rag.build_index(records, vecs), records


class TestExtraction(unittest.TestCase):
    def test_reads_pages_with_numbers(self):
        pages, err = rag.extract_pdf_pages(make_pdf([PAGE1, PAGE2]), "g.pdf")
        self.assertIsNone(err)
        self.assertEqual([p for p, _ in pages], [1, 2])
        self.assertIn("Metformin", pages[1][1])

    def test_bad_files_give_errors_not_crashes(self):
        for data in (b"", b"not a pdf at all", make_pdf([PAGE1])[:200]):
            pages, err = rag.extract_pdf_pages(data, "bad.pdf")
            self.assertEqual(pages, [])
            self.assertTrue(err)

    def test_blank_pdf_is_reported_as_scanned(self):
        pages, err = rag.extract_pdf_pages(make_pdf([""]), "scan.pdf")
        self.assertIn("scanned", err)


class TestChunking(unittest.TestCase):
    def test_chunks_end_on_sentence_boundaries_and_keep_page(self):
        text = " ".join(f"Sentence number {i} talks about blood pressure control." for i in range(60))
        chunks = rag.chunk_pages([(3, text)], chunk_size=300)
        self.assertGreater(len(chunks), 3)
        for c in chunks:
            self.assertEqual(c["page"], 3)
            self.assertTrue(c["text"].endswith("."), c["text"][-20:])
            self.assertLessEqual(len(c["text"]), 300)

    def test_chunks_never_cross_pages(self):
        chunks = rag.chunk_pages([(1, PAGE1), (2, PAGE2)])
        self.assertEqual({c["page"] for c in chunks}, {1, 2})
        self.assertFalse(any("Metformin" in c["text"] for c in chunks if c["page"] == 1))

    def test_huge_sentence_is_wrapped_not_lost(self):
        text = " ".join(["word"] * 1000)
        chunks = rag.chunk_pages([(1, text)], chunk_size=200)
        self.assertEqual(sum(c["text"].count("word") for c in chunks) >= 1000, True)
        self.assertTrue(all(len(c["text"]) <= 200 for c in chunks))

    def test_bad_overlap_raises_instead_of_looping(self):
        with self.assertRaises(ValueError):
            rag.chunk_pages([(1, PAGE1)], overlap_sentences=-1)


class TestSearchAndAnswers(unittest.TestCase):
    def setUp(self):
        self.model, self.index, self.records = index_for([(1, PAGE1), (2, PAGE2)])

    def test_finds_right_page(self):
        hits = rag.search(self.index, self.model, "preferred initial agent for type 2 diabetes", self.records)
        self.assertEqual(hits[0]["page"], 2)

    def test_off_topic_question_returns_nothing(self):
        hits = rag.search(self.index, self.model, "how to repair a bicycle tire", self.records)
        self.assertEqual(hits, [])
        answer, cites = rag.generate_answer("bike?", hits)
        self.assertEqual(answer, rag.NOT_FOUND)
        self.assertEqual(cites, [])

    def test_local_mode_quotes_passages_with_page_labels(self):
        hits = rag.search(self.index, self.model, "metformin diabetes", self.records)
        answer, cites = rag.generate_answer("q", hits)
        self.assertIn("guide.pdf · p. 2", answer)
        self.assertEqual(cites, hits)

    def test_ai_mode_cites_only_passages_it_used(self):
        hits = [{"source": "a.pdf", "page": 4, "chunk": 0, "text": "x", "score": .9},
                {"source": "b.pdf", "page": 7, "chunk": 1, "text": "y", "score": .8}]
        with mock.patch.object(rag, "llm_complete", return_value="Use metformin first [2]."):
            answer, cites = rag.generate_answer("q", hits, api_key="k")
        self.assertEqual(answer, "Use metformin first (b.pdf · p. 7).")
        self.assertEqual([c["source"] for c in cites], ["b.pdf"])

    def test_ai_refusal_shows_no_citations(self):
        hits = [{"source": "a.pdf", "page": 1, "chunk": 0, "text": "x", "score": .9}]
        with mock.patch.object(rag, "llm_complete", return_value=rag.NOT_FOUND):
            answer, cites = rag.generate_answer("q", hits, api_key="k")
        self.assertEqual((answer, cites), (rag.NOT_FOUND, []))

    def test_ai_failure_falls_back_to_passages(self):
        hits = [{"source": "a.pdf", "page": 1, "chunk": 0, "text": "x", "score": .9}]
        with mock.patch.object(rag, "llm_complete", side_effect=RuntimeError("quota")):
            answer, cites = rag.generate_answer("q", hits, api_key="k")
        self.assertIn("quota", answer)
        self.assertEqual(cites, hits)


class TestSummary(unittest.TestCase):
    def test_summary_prompt_forbids_added_advice(self):
        captured = {}

        def fake(prompt, *a, **k):
            captured["p"] = prompt
            return "- point (p. 1)"
        with mock.patch.object(rag, "llm_complete", side_effect=fake):
            _, covered = rag.summarize_pages([(1, PAGE1), (2, PAGE2)], "g.pdf", api_key="k")
        self.assertIn("Do not add advice", captured["p"])
        self.assertNotIn("lifestyle suggestions that", captured["p"])
        self.assertEqual(covered, "all pages")



class TestPolish(unittest.TestCase):
    def test_weak_runner_ups_are_dropped(self):
        class FixedIndex:
            ntotal = 3
            def search(self, q, k):
                return [0.80, 0.75, 0.50], [0, 1, 2]
        recs = [{"source": "a.pdf", "page": p, "chunk": p, "text": "t"} for p in (1, 2, 3)]
        with mock.patch.object(rag, "embed_texts", return_value=np.ones((1, 4), dtype="float32")):
            hits = rag.search(FixedIndex(), None, "q", recs)
        self.assertEqual([h["page"] for h in hits], [1, 2])

    def test_citation_tags_are_unique(self):
        cites = [{"source": "a.pdf", "page": 1}, {"source": "a.pdf", "page": 1}, {"source": "a.pdf", "page": 2}]
        self.assertEqual(rag.unique_labels(cites), ["a.pdf · p. 1", "a.pdf · p. 2"])

if __name__ == "__main__":
    unittest.main()
