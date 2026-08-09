"""Standalone pipeline test: chunking, embedding, and retrieval — no Streamlit required.

Run: python demo.py
"""

from app import build_faiss_index, chunk_text, embed_chunks, load_embedding_model, search_index

SAMPLE_TEXT = """
Hypertension Management Guidelines

Hypertension is defined as a sustained systolic blood pressure of 130 mmHg or higher,
or a diastolic blood pressure of 80 mmHg or higher, measured on at least two separate
occasions. Lifestyle modification is recommended as first-line intervention for all
patients, including sodium restriction, weight loss, regular aerobic exercise, and
reduction in alcohol consumption.

For patients who do not achieve target blood pressure through lifestyle changes alone,
pharmacologic therapy should be initiated. First-line antihypertensive agents include
thiazide diuretics, calcium channel blockers, and ACE inhibitors or angiotensin
receptor blockers. Beta-blockers are generally reserved for patients with a compelling
comorbid indication such as coronary artery disease or heart failure with reduced
ejection fraction.

Type 2 Diabetes Mellitus: Screening and Diagnosis

Screening for type 2 diabetes is recommended for adults aged 35 to 70 who are
overweight or obese. Diagnostic criteria include a fasting plasma glucose of 126 mg/dL
or higher, a two-hour plasma glucose of 200 mg/dL or higher during an oral glucose
tolerance test, a hemoglobin A1c of 6.5% or higher, or a random plasma glucose of
200 mg/dL or higher in a patient with classic symptoms of hyperglycemia.

Metformin remains the preferred initial pharmacologic agent for most patients with
type 2 diabetes, given its efficacy, low hypoglycemia risk, and favorable cost profile.
For patients with established cardiovascular disease or chronic kidney disease,
consider a GLP-1 receptor agonist or SGLT2 inhibitor with demonstrated cardiovascular
or renal benefit, independent of glycemic control.
""".strip()

QUERIES = [
    "What is the first-line treatment for hypertension?",
    "What is the preferred initial medication for type 2 diabetes?",
]


def main():
    print("=" * 70)
    print("MedRAG pipeline demo (chunking -> embedding -> retrieval)")
    print("=" * 70)

    print("\n[1/4] Chunking sample text...")
    chunks = chunk_text(SAMPLE_TEXT)
    print(f"  -> {len(chunks)} chunk(s) created")
    for i, c in enumerate(chunks):
        print(f"  chunk {i} ({len(c)} chars): {c[:90]}...")

    print("\n[2/4] Loading embedding model (all-MiniLM-L6-v2)...")
    model = load_embedding_model()
    print("  -> model loaded")

    print("\n[3/4] Embedding chunks...")
    embeddings = embed_chunks(model, chunks)
    print(f"  -> embeddings shape: {embeddings.shape}")

    print("\n[4/4] Building FAISS index and running sample queries...")
    index = build_faiss_index(embeddings.shape[1])
    index.add(embeddings)
    print(f"  -> index contains {index.ntotal} vectors")

    chunk_records = [
        {"source": "sample.txt", "chunk_index": i, "text": c} for i, c in enumerate(chunks)
    ]

    for query in QUERIES:
        print(f"\n  Query: '{query}'")
        results = search_index(index, model, query, chunk_records, top_k=2)
        for r in results:
            print(f"    [{r['source']} chunk {r['chunk_index']}] distance={r['distance']:.4f}")
            print(f"    {r['text'][:150]}...")

    print("\n" + "=" * 70)
    print("Demo complete — chunking, embedding, and retrieval all working.")
    print("=" * 70)


if __name__ == "__main__":
    main()
