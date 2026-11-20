"""Standalone pipeline check: chunking, embedding, retrieval, citations. No Streamlit needed.

Run: python demo.py
"""

import os

import rag

SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples", "sample_guideline.txt")
QUERIES = [
    "What is the first-line treatment for hypertension?",
    "What is the preferred initial medication for type 2 diabetes?",
    "How do I fix a flat bicycle tire?",  # should be refused: not in the document
]


def load_sample_pages():
    raw = open(SAMPLE, encoding="utf-8").read()
    pages = []
    for block in raw.split("=== page ")[1:]:
        number, _, text = block.partition("===")
        pages.append((int(number.strip()), " ".join(text.split())))
    return pages


def main():
    pages = load_sample_pages()
    chunks = rag.chunk_pages(pages)
    print(f"{len(pages)} pages -> {len(chunks)} passages")
    model = rag.load_embedding_model()
    vecs = rag.embed_texts(model, [c["text"] for c in chunks])
    records = [{"source": "sample-guideline", "page": c["page"], "chunk": i, "text": c["text"]}
               for i, c in enumerate(chunks)]
    index = rag.build_index(records, vecs)
    for q in QUERIES:
        hits = rag.search(index, model, q, records)
        answer, cites = rag.generate_answer(q, hits)
        print(f"\nQ: {q}")
        if not cites:
            print(f"  -> {answer}")
        for c in cites:
            print(f"  [{rag.citation_label(c)}] score {c['score']}: {c['text'][:110]}...")


if __name__ == "__main__":
    main()
