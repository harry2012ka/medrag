"""MedRAG — Streamlit RAG app for clinical PDF Q&A."""

import io
import os
import re

import faiss
import numpy as np
import streamlit as st
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 4

PROVIDERS = {
    "OpenAI": {"env": "OPENAI_API_KEY", "model": "gpt-4o-mini"},
    "Claude": {"env": "ANTHROPIC_API_KEY", "model": "claude-haiku-4-5-20251001"},
}

# ---------------------------------------------------------------------------
# Core RAG functions (no Streamlit dependency — reused by demo.py)
# ---------------------------------------------------------------------------


def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == length:
            break
        start = end - overlap
    return chunks


def extract_pdf_text(file_bytes, filename):
    """Returns (text, error_message). error_message is None on success."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as e:
        return "", f"Could not read '{filename}' — the file may be corrupted ({e})."

    if reader.is_encrypted:
        try:
            result = reader.decrypt("")
        except Exception:
            result = 0
        if not result:
            return "", f"'{filename}' is password-protected and could not be opened."

    text_parts = []
    for page in reader.pages:
        try:
            text_parts.append(page.extract_text() or "")
        except Exception:
            text_parts.append("")
    text = "\n".join(text_parts).strip()

    if not text:
        return "", (
            f"'{filename}' has no extractable text — it may be a scanned/"
            "image-only PDF. Try running it through OCR first."
        )
    return text, None


def _embedding_dim(model):
    if hasattr(model, "get_embedding_dimension"):
        return model.get_embedding_dimension()
    return model.get_sentence_embedding_dimension()


def embed_chunks(model, chunks):
    if not chunks:
        return np.zeros((0, _embedding_dim(model)), dtype="float32")
    embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.astype("float32")


def build_faiss_index(dim):
    return faiss.IndexFlatL2(dim)


def search_index(index, model, query, chunk_records, top_k=TOP_K):
    if index is None or index.ntotal == 0:
        return []
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")
    k = min(top_k, index.ntotal)
    distances, indices = index.search(query_vec, k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        record = chunk_records[idx]
        results.append({**record, "distance": float(dist)})
    return results


def llm_complete(prompt, api_key, provider="OpenAI"):
    """Single-turn completion via the chosen provider. Raises on failure."""
    model = PROVIDERS[provider]["model"]
    if provider == "Claude":
        from anthropic import Anthropic

        response = Anthropic(api_key=api_key).messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in response.content if b.type == "text").strip()

    from openai import OpenAI

    response = OpenAI(api_key=api_key).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def summarize_document(text, filename, api_key=None, provider="OpenAI"):
    if api_key:
        try:
            truncated = text[:12000]
            prompt = (
                "Summarize the following clinical document in 3-5 concise bullet points. "
                "Stick strictly to facts present in the text — do not add outside "
                "information.\n\n"
                "Then add a 'General lifestyle considerations' section with a few general, "
                "non-prescriptive lifestyle suggestions that relate to the document's "
                "topic (e.g. diet, exercise, monitoring habits) — keep these general, not "
                "individualized medical advice.\n\n"
                "End with this exact line on its own: '⚠️ This summary is for reference "
                "only. Please consult your physician before making any changes based on "
                "this information.'\n\n"
                f"Document:\n{truncated}"
            )
            return llm_complete(prompt, api_key, provider)
        except Exception as e:
            return f"_(Summary generation failed: {e})_"

    preview = text[:400].strip()
    return (
        "_(Add an OpenAI or Claude key in the sidebar for an automatic AI summary with lifestyle "
        f"suggestions. Showing a preview of the document instead:)_\n\n{preview}...\n\n"
        "⚠️ This is a raw excerpt, not a summary. Please consult your physician before "
        "making any changes based on this information."
    )


def _fallback_answer(retrieved):
    parts = [
        f"**From {r['source']} (chunk {r['chunk_index']}):**\n{r['text']}"
        for r in retrieved
    ]
    return "\n\n---\n\n".join(parts)


def generate_answer(query, retrieved, api_key=None, provider="OpenAI"):
    """Returns (answer_text, citations)."""
    if not retrieved:
        return "I couldn't find anything relevant in the uploaded documents.", []

    citations = [
        {"source": r["source"], "chunk_index": r["chunk_index"]} for r in retrieved
    ]

    if api_key:
        try:
            context_block = "\n\n".join(
                f"[Source: {r['source']}, chunk {r['chunk_index']}]\n{r['text']}"
                for r in retrieved
            )
            prompt = (
                "You are a clinical reference assistant. Answer the question using "
                "ONLY the context below. Cite sources inline like (source, chunk N). "
                "If the context doesn't contain the answer, say so plainly.\n\n"
                f"Context:\n{context_block}\n\nQuestion: {query}\n\nAnswer:"
            )
            return llm_complete(prompt, api_key, provider), citations
        except Exception as e:
            fallback = _fallback_answer(retrieved)
            return (
                f"_({provider} generation failed: {e}. Showing retrieved passages instead.)_"
                f"\n\n{fallback}",
                citations,
            )

    return _fallback_answer(retrieved), citations


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
:root {
    --medrag-accent: #0f766e;
    --medrag-accent-light: #ccfbf1;
}
.stApp {
    background-color: #f8fafc;
}
section[data-testid="stSidebar"] {
    background-color: #ecfeff;
    border-right: 1px solid #99f6e4;
}
h1, h2, h3 {
    color: #115e59;
}
.medrag-disclaimer {
    background-color: #fffbeb;
    border: 1px solid #fde68a;
    color: #92400e;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}
.medrag-citation {
    background-color: var(--medrag-accent-light);
    color: #115e59;
    border-radius: 0.4rem;
    padding: 0.15rem 0.5rem;
    font-size: 0.8rem;
    margin-right: 0.3rem;
    display: inline-block;
}
div[data-testid="stChatMessage"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 0.6rem;
}
</style>
"""


@st.cache_resource(show_spinner=False)
def get_embedding_model():
    return load_embedding_model()


def _citation_label(c):
    if c["chunk_index"] == "summary":
        return f'{c["source"]} · full document'
    return f'{c["source"]} · chunk {c["chunk_index"]}'


def _render_citations(citations):
    tags = "".join(
        f'<span class="medrag-citation">{_citation_label(c)}</span>' for c in citations
    )
    st.markdown(tags, unsafe_allow_html=True)


def init_session_state():
    defaults = {
        "documents": {},  # filename -> chunk count
        "chunk_records": [],  # list of {source, chunk_index, text}
        "index": None,
        "dim": None,
        "processed_keys": set(),
        "errors": [],
        "messages": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_documents():
    st.session_state.documents = {}
    st.session_state.chunk_records = []
    st.session_state.index = None
    st.session_state.dim = None
    st.session_state.processed_keys = set()
    st.session_state.errors = []


def process_uploaded_files(uploaded_files, api_key=None, provider="OpenAI"):
    new_files = [
        f for f in uploaded_files if (f.name, f.size) not in st.session_state.processed_keys
    ]
    if not new_files:
        return

    status = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0)
    status.info("Processing...")

    model = get_embedding_model()

    for i, f in enumerate(new_files):
        try:
            file_bytes = f.read()
            text, error = extract_pdf_text(file_bytes, f.name)
            if error:
                st.session_state.errors.append(error)
            else:
                chunks = chunk_text(text)
                if not chunks:
                    st.session_state.errors.append(
                        f"'{f.name}' produced no usable text chunks."
                    )
                else:
                    embeddings = embed_chunks(model, chunks)
                    if st.session_state.index is None:
                        st.session_state.dim = embeddings.shape[1]
                        st.session_state.index = build_faiss_index(st.session_state.dim)
                    st.session_state.index.add(embeddings)
                    for ci, chunk in enumerate(chunks):
                        st.session_state.chunk_records.append(
                            {"source": f.name, "chunk_index": ci, "text": chunk}
                        )
                    st.session_state.documents[f.name] = len(chunks)

                    summary = summarize_document(text, f.name, api_key=api_key, provider=provider)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"**Summary of {f.name}:**\n\n{summary}",
                            "citations": [{"source": f.name, "chunk_index": "summary"}],
                        }
                    )
        except Exception as e:
            st.session_state.errors.append(f"Unexpected error processing '{f.name}': {e}")
        finally:
            st.session_state.processed_keys.add((f.name, f.size))
            progress_bar.progress((i + 1) / len(new_files))

    status.success("Processing complete.")


def render_sidebar():
    st.sidebar.title("MedRAG")
    st.sidebar.caption("Clinical document Q&A")

    st.sidebar.subheader("Generation (optional)")
    provider = st.sidebar.selectbox("Provider", list(PROVIDERS))
    env_name = PROVIDERS[provider]["env"]
    env_key = os.environ.get(env_name)
    if not env_key:
        try:
            env_key = st.secrets.get(env_name)
        except Exception:
            env_key = None
    typed_key = st.sidebar.text_input(
        f"{provider} API key",
        type="password",
        help=f"Add a key for AI-generated answers and document summaries, or set {env_name}. Leave blank to use free local retrieval-only mode.",
    )
    api_key = typed_key or env_key
    if api_key and not typed_key:
        st.sidebar.caption(f"Using {env_name} from the environment.")

    uploaded_files = st.sidebar.file_uploader(
        "Upload clinical PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        process_uploaded_files(uploaded_files, api_key=api_key or None, provider=provider)

    if st.session_state.errors:
        for err in st.session_state.errors:
            st.sidebar.error(err)

    st.sidebar.subheader("Indexed documents")
    if st.session_state.documents:
        for name, count in st.session_state.documents.items():
            st.sidebar.write(f"📄 {name} — {count} chunks")
    else:
        st.sidebar.caption("No documents indexed yet.")

    st.sidebar.divider()
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if col2.button("Reset all documents", use_container_width=True):
        reset_documents()
        st.rerun()

    return api_key, provider


def render_chat():
    st.title("🩺 MedRAG")
    st.markdown(
        '<div class="medrag-disclaimer">⚠️ This tool provides reference support only '
        "and is not a substitute for clinical judgment. Always verify against primary "
        "sources and use professional discretion.</div>",
        unsafe_allow_html=True,
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                _render_citations(msg["citations"])

    query = st.chat_input("Ask a question about the uploaded documents...")
    if not query:
        return

    st.session_state.messages.append({"role": "user", "content": query, "citations": []})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        if not st.session_state.documents:
            answer = "Please upload at least one PDF in the sidebar before asking questions."
            citations = []
            st.markdown(answer)
        else:
            with st.spinner("Searching documents..."):
                model = get_embedding_model()
                retrieved = search_index(
                    st.session_state.index, model, query, st.session_state.chunk_records
                )
                answer, citations = generate_answer(
                    query,
                    retrieved,
                    api_key=st.session_state.get("api_key"),
                    provider=st.session_state.get("provider", "OpenAI"),
                )
            st.markdown(answer)
            if citations:
                _render_citations(citations)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "citations": citations}
    )


def main():
    st.set_page_config(page_title="MedRAG", page_icon="🩺", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()

    api_key, provider = render_sidebar()
    st.session_state["api_key"] = api_key or None
    st.session_state["provider"] = provider

    render_chat()


if __name__ == "__main__":
    main()
