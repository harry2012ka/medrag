"""MedRAG core: extraction, chunking, retrieval, answers. No Streamlit dependency.

Design rules (see CLAUDE.md):
  - The free/local path works with no API key.
  - Bad PDFs never crash anything; callers get an error message instead.
  - Every answer cites source file + page, and only the passages it actually used.
"""

import hashlib
import io
import re

import numpy as np

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800          # target characters per chunk
CHUNK_OVERLAP = 1         # sentences carried over between neighbouring chunks
TOP_K = 4
# Cosine similarity below this is treated as "not about your documents".
# all-MiniLM-L6-v2 scores unrelated text around 0.0-0.2 and on-topic passages 0.35+.
MIN_SCORE = 0.30
# Also drop passages much weaker than the best match, so only the clearly relevant ones show.
MAX_GAP_FROM_BEST = 0.12

PROVIDERS = {
    "OpenAI": {"env": "OPENAI_API_KEY", "model": "gpt-4o-mini"},
    "Claude": {"env": "ANTHROPIC_API_KEY", "model": "claude-haiku-4-5-20251001"},
}

NOT_FOUND = (
    "I couldn't find this in your documents. Try rephrasing, or upload the document "
    "that covers it. I won't answer clinical questions from outside your sources."
)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


# ── Extraction ────────────────────────────────────────────────────────────────

def doc_id(file_bytes):
    return hashlib.sha1(file_bytes).hexdigest()[:10]


def extract_pdf_pages(file_bytes, filename):
    """Returns (pages, error). pages = [(page_number, text), ...], page numbers start at 1."""
    try:
        from pypdf import PdfReader
    except ImportError:  # older installs
        from PyPDF2 import PdfReader
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as e:
        return [], f"Could not read '{filename}': the file may be corrupted ({e})."

    if reader.is_encrypted:
        try:
            ok = reader.decrypt("")
        except Exception as e:
            if "cryptography" in str(e).lower() or "AES" in str(e):
                return [], f"'{filename}' uses encryption this server can't open. Save an unencrypted copy and try again."
            ok = 0
        if not ok:
            return [], f"'{filename}' is password-protected and could not be opened."

    pages = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append((number, text))

    if not pages:
        return [], (f"'{filename}' has no extractable text. It may be a scanned or "
                    "image-only PDF. Try running it through OCR first.")
    return pages, None


# ── Chunking ──────────────────────────────────────────────────────────────────

def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


def _hard_wrap(sentence, size):
    """Split a single over-long 'sentence' (tables, lists) at word boundaries."""
    words, out, cur = sentence.split(" "), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > size:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_pages(pages, chunk_size=CHUNK_SIZE, overlap_sentences=CHUNK_OVERLAP):
    """Sentence-aware chunks that never cross a page, so every chunk has one page number.

    Returns [{"page": n, "text": str}, ...].
    """
    if overlap_sentences < 0:
        raise ValueError("overlap_sentences must be >= 0")
    chunks = []
    for page, text in pages:
        sentences = []
        for s in split_sentences(text):
            sentences.extend(_hard_wrap(s, chunk_size) if len(s) > chunk_size else [s])
        current = []
        for s in sentences:
            if current and len(" ".join(current + [s])) > chunk_size:
                chunks.append({"page": page, "text": " ".join(current)})
                keep = current[-overlap_sentences:] if overlap_sentences else []
                # never let the carried-over part alone fill a chunk (no infinite growth)
                current = keep if len(" ".join(keep + [s])) <= chunk_size else []
            current.append(s)
        if current:
            chunks.append({"page": page, "text": " ".join(current)})
    return chunks


# ── Embeddings & search ───────────────────────────────────────────────────────

def load_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(model, texts):
    """Unit-length float32 vectors, so a dot product is cosine similarity."""
    if not texts:
        return np.zeros((0, 1), dtype="float32")
    vecs = np.asarray(model.encode(texts, convert_to_numpy=True, show_progress_bar=False), dtype="float32")
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


class VectorIndex:
    """Cosine-similarity index. Uses FAISS when installed, plain numpy otherwise."""

    def __init__(self, dim):
        self.dim = dim
        self._vecs = np.zeros((0, dim), dtype="float32")
        try:
            import faiss
            self._faiss = faiss.IndexFlatIP(dim)
        except ImportError:
            self._faiss = None

    @property
    def ntotal(self):
        return self._vecs.shape[0]

    def add(self, vecs):
        self._vecs = np.vstack([self._vecs, vecs]).astype("float32")
        if self._faiss is not None:
            self._faiss.add(vecs)

    def search(self, query_vec, k):
        k = min(k, self.ntotal)
        if k == 0:
            return [], []
        if self._faiss is not None:
            scores, idx = self._faiss.search(query_vec.reshape(1, -1), k)
            return list(scores[0]), list(idx[0])
        scores = self._vecs @ query_vec.reshape(-1)
        order = np.argsort(-scores)[:k]
        return [float(scores[i]) for i in order], [int(i) for i in order]


def build_index(records, vecs):
    index = VectorIndex(vecs.shape[1])
    if len(records):
        index.add(vecs)
    return index


def search(index, model, query, records, top_k=TOP_K, min_score=MIN_SCORE, max_gap=MAX_GAP_FROM_BEST):
    """Top passages above the relevance cutoff, best first. [] means 'not in your documents'."""
    if index is None or index.ntotal == 0 or not query.strip():
        return []
    qvec = embed_texts(model, [query])[0]
    scores, ids = index.search(qvec, top_k)
    out = []
    for score, i in zip(scores, ids):
        if i < 0 or score < min_score:
            continue
        out.append({**records[i], "score": round(float(score), 3)})
    if out:
        best = max(r["score"] for r in out)
        out = [r for r in out if r["score"] >= best - max_gap]
    return out


# ── Answers ───────────────────────────────────────────────────────────────────

def citation_label(r):
    return f'{r["source"]} · p. {r["page"]}'


def unique_labels(citations):
    """One tag per file+page, in order of first appearance."""
    seen, out = set(), []
    for c in citations:
        label = citation_label(c)
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out


def llm_complete(prompt, api_key, provider="OpenAI", history=None):
    """Single completion via the chosen provider. Raises on failure."""
    model = PROVIDERS[provider]["model"]
    messages = list(history or []) + [{"role": "user", "content": prompt}]
    if provider == "Claude":
        from anthropic import Anthropic
        resp = Anthropic(api_key=api_key).messages.create(model=model, max_tokens=1024, messages=messages)
        return "".join(b.text for b in resp.content if b.type == "text").strip()
    from openai import OpenAI
    resp = OpenAI(api_key=api_key).chat.completions.create(model=model, messages=messages, temperature=0.1)
    return resp.choices[0].message.content.strip()


def answer_prompt(query, retrieved):
    context = "\n\n".join(
        f"[{n}] ({citation_label(r)})\n{r['text']}" for n, r in enumerate(retrieved, start=1)
    )
    return (
        "You are a clinical reference assistant for clinicians. Answer ONLY from the numbered "
        "passages below. After each statement, cite the passage number in square brackets, "
        "for example [1] or [2][3]. Do not add facts, doses, or recommendations that are not "
        "in the passages. If the passages don't answer the question, reply exactly: "
        f"\"{NOT_FOUND}\"\n\n"
        f"Passages:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    )


def used_passages(answer, retrieved):
    """Passages the answer actually cites ([n] markers); all of them if it cites none."""
    nums = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    used = [r for n, r in enumerate(retrieved, start=1) if n in nums]
    return used or retrieved


def link_markers(answer, retrieved):
    """Replace [n] markers with readable (file · p. N) labels."""
    def sub(m):
        n = int(m.group(1))
        return f"({citation_label(retrieved[n - 1])})" if 1 <= n <= len(retrieved) else m.group(0)
    return re.sub(r"\[(\d+)\]", sub, answer)


def local_answer(retrieved):
    return "Here are the most relevant passages from your documents:\n\n" + "\n\n".join(
        f"**{citation_label(r)}**\n> {r['text']}" for r in retrieved
    )


def generate_answer(query, retrieved, api_key=None, provider="OpenAI", history=None):
    """Returns (answer_markdown, citations). citations = the passages actually used."""
    if not retrieved:
        return NOT_FOUND, []
    if not api_key:
        return local_answer(retrieved), retrieved
    try:
        raw = llm_complete(answer_prompt(query, retrieved), api_key, provider, history=history)
    except Exception as e:
        return f"_({provider} answer failed: {e}. Showing the passages instead.)_\n\n{local_answer(retrieved)}", retrieved
    if NOT_FOUND[:40] in raw:
        return NOT_FOUND, []
    return link_markers(raw, retrieved), used_passages(raw, retrieved)


SUMMARY_CHARS = 12000


def summarize_pages(pages, filename, api_key=None, provider="OpenAI"):
    """(summary_markdown, page_range_label). Facts from the document only, no added advice."""
    text, last_page = "", 0
    for page, t in pages:
        if len(text) >= SUMMARY_CHARS:
            break
        text += f"\n[page {page}] {t}"
        last_page = page
    covered = f"pages 1-{last_page}" if last_page < pages[-1][0] else "all pages"
    if not api_key:
        preview = pages[0][1][:400]
        return (f"_Add an API key for an AI summary. First lines of the document:_\n\n> {preview}…", "page 1")
    prompt = (
        "Summarize this clinical document for a clinician in 3-5 bullet points. Use ONLY facts "
        "stated in the text. Do not add advice, lifestyle suggestions, or anything not in the "
        "document. End each bullet with the page it came from, like (p. 3).\n\n"
        f"Document ({covered}):{text}"
    )
    try:
        return llm_complete(prompt, api_key, provider), covered
    except Exception as e:
        return f"_(Summary failed: {e})_", covered
