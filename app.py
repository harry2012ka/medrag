"""MedRAG — Streamlit UI for clinical PDF Q&A. All RAG logic lives in rag.py."""

import datetime
import html
import os

import numpy as np
import streamlit as st

import rag

SAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples", "sample_guideline.txt")
SAMPLE_NAME = "sample-guideline (demo)"
SAMPLE_QUESTIONS = [
    "What blood pressure counts as hypertension?",
    "What is the preferred first medication for type 2 diabetes?",
    "When are beta-blockers used for high blood pressure?",
]
# AI answers per visitor session when the app uses the server's own key
SERVER_KEY_LIMIT = int(os.environ.get("MEDRAG_MAX_AI_ANSWERS", "15"))

CUSTOM_CSS = """
<style>
.stApp { background-color: #f8fafc; }
section[data-testid="stSidebar"] { background-color: #ecfeff; border-right: 1px solid #99f6e4; }
h1, h2, h3 { color: #115e59; }
.medrag-note { background:#fffbeb; border:1px solid #fde68a; color:#92400e; padding:.7rem 1rem;
  border-radius:.5rem; font-size:.9rem; margin-bottom:.6rem; }
.medrag-citation { background:#ccfbf1; color:#115e59; border-radius:.4rem; padding:.15rem .5rem;
  font-size:.8rem; margin-right:.3rem; display:inline-block; }
div[data-testid="stChatMessage"] { background:#fff; border:1px solid #e2e8f0; border-radius:.6rem; }
</style>
"""


# ── Model ─────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading the search model (first run only)…")
def get_embedding_model():
    return rag.load_embedding_model()


def model_or_stop():
    try:
        return get_embedding_model()
    except Exception as e:
        st.error(f"The search model couldn't load ({e}). Refresh the page in a minute; if it keeps "
                 "happening, the server can't reach Hugging Face or is out of memory.")
        st.stop()


# ── Documents ─────────────────────────────────────────────────────────────────

def init_state():
    defaults = {"docs": {}, "index": None, "records": [], "errors": {}, "messages": [], "ai_used": 0,
                "audience": "clinician"}
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _display_name(filename, doc_key):
    taken = {d["name"] for k, d in st.session_state.docs.items() if k != doc_key}
    name, n = filename, 2
    while name in taken:
        name = f"{filename} ({n})"
        n += 1
    return name


def rebuild_index():
    records, vecs = [], []
    for d in st.session_state.docs.values():
        records.extend(d["records"])
        vecs.append(d["vecs"])
    st.session_state.records = records
    st.session_state.index = rag.build_index(records, np.vstack(vecs)) if records else None


def add_document(doc_key, filename, pages, api_key, provider):
    model = model_or_stop()
    name = _display_name(filename, doc_key)
    chunks = rag.chunk_pages(pages)
    if not chunks:
        st.session_state.errors[doc_key] = f"'{filename}' produced no usable text."
        return
    vecs = rag.embed_texts(model, [c["text"] for c in chunks])
    records = [{"source": name, "page": c["page"], "chunk": i, "text": c["text"]} for i, c in enumerate(chunks)]
    full_text = " ".join(t for _, t in pages)
    phi = rag.find_phi(full_text)
    st.session_state.docs[doc_key] = {"name": name, "pages": len(pages), "chunks": len(chunks),
                                      "records": records, "vecs": vecs, "phi": phi,
                                      "names": sorted(rag.names_in(full_text))}
    summary, covered = rag.summarize_pages(pages, name, api_key=api_key, provider=provider)
    st.session_state.messages.append({"role": "assistant", "content": f"**Summary of {name}** ({covered})\n\n{summary}",
                                      "citations": [], "summary": True})


def sync_uploads(uploaded_files, api_key, provider):
    """Index new files, drop files removed from the uploader. Bad files never crash the app."""
    current = {}
    for f in uploaded_files or []:
        data = f.getvalue()
        current[rag.doc_id(data)] = (f.name, data)

    removed = [k for k in st.session_state.docs if k not in current and k != "sample"]
    for k in removed:
        st.session_state.docs.pop(k)
    for k in [k for k in st.session_state.errors if k not in current]:
        st.session_state.errors.pop(k)

    new = [(k, v) for k, v in current.items() if k not in st.session_state.docs and k not in st.session_state.errors]
    if new:
        bar = st.sidebar.progress(0.0, text="Reading documents…")
        for i, (k, (name, data)) in enumerate(new):
            try:
                pages, err = rag.extract_pdf_pages(data, name)
                if err:
                    st.session_state.errors[k] = err
                else:
                    add_document(k, name, pages, api_key, provider)
            except Exception as e:
                st.session_state.errors[k] = f"Unexpected error reading '{name}': {e}"
            bar.progress((i + 1) / len(new), text=f"Indexed {i + 1} of {len(new)}")
        bar.empty()
    if removed or new:
        rebuild_index()


def load_sample(api_key, provider):
    if "sample" in st.session_state.docs:
        return
    raw = open(SAMPLE_PATH, encoding="utf-8").read()
    pages = []
    for block in raw.split("=== page ")[1:]:
        number, _, text = block.partition("===")
        pages.append((int(number.strip()), " ".join(text.split())))
    add_document("sample", SAMPLE_NAME, pages, api_key, provider)
    rebuild_index()


# ── Keys ──────────────────────────────────────────────────────────────────────

def get_server_key():
    for provider, cfg in rag.PROVIDERS.items():
        key = os.environ.get(cfg["env"])
        if not key:
            try:
                key = st.secrets.get(cfg["env"])
            except Exception:
                key = None
        if key:
            return provider, key
    return None, None


# ── UI ────────────────────────────────────────────────────────────────────────

def render_citations(citations):
    if not citations:
        return
    st.markdown("".join(f'<span class="medrag-citation">{html.escape(label)}</span>'
                        for label in rag.unique_labels(citations)), unsafe_allow_html=True)
    with st.expander("Show the source passages"):
        for c in citations:
            st.markdown(f"**{rag.citation_label(c)}** · match {c.get('similarity', c.get('score', 0)):.2f}\n\n> {c['text']}")


def render_sidebar():
    st.sidebar.title("MedRAG")
    st.sidebar.caption("Ask your clinical documents a question.")
    reader = st.sidebar.radio("Who's reading?", ["Clinician", "Patient"], horizontal=True,
                              help="Patient mode explains answers in plain language. Answers still "
                                   "come only from your documents.")
    st.session_state.audience = reader.lower()

    server_provider, server_key = get_server_key()
    if server_provider:
        provider, api_key, using_server_key = server_provider, server_key, True
    else:
        st.sidebar.subheader("AI answers (optional)")
        provider = st.sidebar.selectbox("Provider", list(rag.PROVIDERS))
        api_key = st.sidebar.text_input(f"{provider} API key", type="password",
                                        help="Leave blank for free local mode: you get the exact passages, no AI writing.")
        using_server_key = False

    uploaded = st.sidebar.file_uploader("Upload clinical PDFs", type=["pdf"], accept_multiple_files=True)
    sync_uploads(uploaded, api_key or None, provider)

    if st.sidebar.button("Try the sample document", use_container_width=True):
        load_sample(api_key or None, provider)

    for err in st.session_state.errors.values():
        st.sidebar.error(err)

    st.sidebar.subheader("Indexed documents")
    if st.session_state.docs:
        for d in st.session_state.docs.values():
            st.sidebar.write(f"📄 {d['name']}: {d['pages']} pages, {d['chunks']} passages")
            if d.get("phi"):
                st.sidebar.warning(
                    f"Possible patient identifiers in {d['name']}: {rag.describe_phi(d['phi'])}. "
                    "They're hidden before anything is sent to the AI, but this server still holds the "
                    "file for your session. Use a de-identified copy if you can.")
    else:
        st.sidebar.caption("Nothing indexed yet.")

    st.sidebar.divider()
    if any(not m.get("summary") for m in st.session_state.messages):
        st.sidebar.download_button("Download this conversation", transcript_markdown(),
                                   file_name="medrag-conversation.md", mime="text/markdown",
                                   use_container_width=True)
    c1, c2 = st.sidebar.columns(2)
    if c1.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if c2.button("Reset all", use_container_width=True):
        for k in ("docs", "index", "records", "errors", "messages"):
            st.session_state.pop(k, None)
        st.rerun()

    if using_server_key and st.session_state.ai_used >= SERVER_KEY_LIMIT:
        st.sidebar.info("AI answer limit for this demo reached. You'll still get the exact source passages.")
        api_key = None
    return api_key or None, provider, using_server_key


def known_names():
    """Patient names found (with a label) anywhere in the uploaded documents."""
    return {n for d in st.session_state.docs.values() for n in d.get("names", [])}


def transcript_markdown():
    """The conversation with its citations, for saving or sharing."""
    lines = ["# MedRAG conversation", "",
             f"_Saved {datetime.datetime.now():%Y-%m-%d %H:%M}. Answers come only from the uploaded "
             "documents; check each cited page. Not a substitute for clinical judgment._", ""]
    docs = ", ".join(d["name"] for d in st.session_state.docs.values()) or "none"
    lines += [f"**Documents:** {docs}", ""]
    for m in st.session_state.messages:
        who = "Question" if m["role"] == "user" else ("Summary" if m.get("summary") else "Answer")
        lines += [f"## {who}", "", m["content"], ""]
        labels = rag.unique_labels(m.get("citations") or [])
        if labels:
            lines += ["Sources: " + "; ".join(labels), ""]
    return "\n".join(lines)


def history_for_llm(limit=4):
    """Last few question/answer pairs (oldest first, alternating, starting with a question)
    so follow-up questions make sense. Excludes the question being asked right now."""
    turns = [m for m in st.session_state.messages[:-1] if not m.get("summary")]
    out = []
    for m in turns:
        if out and out[-1]["role"] == m["role"]:
            out[-1] = {"role": m["role"], "content": m["content"]}
        else:
            out.append({"role": m["role"], "content": m["content"]})
    out = out[-2 * limit:]
    while out and out[0]["role"] != "user":
        out.pop(0)
    if out and out[-1]["role"] == "user":
        out.pop()
    return out


def ask(query, api_key, provider, using_server_key):
    st.session_state.messages.append({"role": "user", "content": query, "citations": []})
    with st.chat_message("user"):
        st.markdown(query)
    audience = st.session_state.get("audience", "clinician")
    with st.chat_message("assistant"):
        strength = ""
        if not st.session_state.docs:
            answer, citations = "Upload a PDF or click **Try the sample document** in the sidebar first.", []
        else:
            with st.spinner("Searching your documents…"):
                model = model_or_stop()
                retrieved = rag.search(st.session_state.index, model, query, st.session_state.records)
                answer, citations = rag.generate_answer(query, retrieved, api_key=api_key, provider=provider,
                                                        history=history_for_llm() if api_key else None,
                                                        audience=audience, known_names=known_names())
                strength = rag.match_strength(citations)
                if api_key and retrieved and using_server_key:
                    st.session_state.ai_used += 1
        urgent = rag.emergency_notice(query)
        if urgent:
            answer = f"{urgent}\n\n{answer}"
        st.markdown(answer)
        if strength:
            st.caption(strength)
        render_citations(citations)
    st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations,
                                      "strength": strength})


def render_chat(api_key, provider, using_server_key):
    st.title("🩺 MedRAG")
    st.markdown(
        ('<div class="medrag-note">⚠️ Reference support for clinicians, not a substitute for clinical judgment. '
         "Answers come only from your documents; always check the cited page.</div>"
         if st.session_state.get("audience") != "patient" else
         '<div class="medrag-note">⚠️ This explains what your documents say. It is not medical advice and can\'t '
         "diagnose you. Talk to your doctor, nurse, or pharmacist before changing anything. In an emergency, call 911.</div>")
        +
        (('<div class="medrag-note">🔒 Don\'t upload documents containing patient names or other identifying '
          "information.") if st.session_state.get("audience") != "patient" else
         '<div class="medrag-note">🔒 Your files stay on this server only while this page is open.')
        + " Likely identifiers (names, birth dates, record numbers) are hidden before anything is sent to "
        f"{html.escape(provider)} to write an answer. In free mode nothing leaves this server.</div>",
        unsafe_allow_html=True,
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("strength"):
                st.caption(msg["strength"])
            render_citations(msg.get("citations"))

    if "sample" in st.session_state.docs:
        cols = st.columns(len(SAMPLE_QUESTIONS))
        for col, q in zip(cols, SAMPLE_QUESTIONS):
            if col.button(q, use_container_width=True):
                st.session_state["pending_question"] = q

    query = st.chat_input("Ask a question about your documents…") or st.session_state.pop("pending_question", None)
    if query:
        ask(query, api_key, provider, using_server_key)


def main():
    st.set_page_config(page_title="MedRAG", page_icon="🩺", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_state()
    api_key, provider, using_server_key = render_sidebar()
    render_chat(api_key, provider, using_server_key)


if __name__ == "__main__":
    main()
