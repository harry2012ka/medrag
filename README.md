# MedRAG

**Ask your clinical documents a question. Get an answer with the exact source and passage it came from.**

**🔗 Try it live: [medrag-production-b839.up.railway.app](https://medrag-production-b839.up.railway.app)** — no install needed, upload a PDF and ask a question.

## 🎥 Demo

> _[Loom demo link — paste here]_

## The problem

Clinical teams sit on huge piles of PDFs — protocols, guidelines, drug monographs, internal SOPs — and finding the one paragraph you need means Ctrl-F-ing through a dozen documents, or worse, relying on memory. General-purpose chatbots either don't have your documents or will happily hallucinate an answer that sounds confident and is wrong. In a clinical setting, an unsourced answer is worse than no answer.

## Who it's for

- Clinicians and clinical staff who need fast, traceable answers from internal guidelines or reference PDFs
- Clinic operations and compliance teams standardizing on protocol documents
- Anyone who wants document Q&A that's private, cheap (or free), and shows its work

## What it does

Upload PDFs (or click **Try the sample document**), then ask questions in a chat. Every answer comes only from your documents and **cites the file and page number**, with the exact quoted passage one click away, so you can check it yourself.

- **Page-level citations.** Each passage is tied to one page. With AI answers on, only the passages the answer actually used are cited.
- **Says "I don't know."** If nothing in your documents is relevant enough, it tells you instead of guessing. It never answers clinical questions from outside your sources.
- **Free by default.** With no API key, it shows the exact relevant passages (nothing leaves the server). Add an OpenAI or Claude key for written answers and per-document summaries.
- **Follow-up questions** work when AI answers are on.
- **Safe with messy files.** Encrypted, scanned, empty or corrupted PDFs show a clear message in the sidebar instead of crashing. Removing a file from the uploader removes it from search.
- **Privacy notice built in.** The app tells users not to upload identifiable patient information and when passages are sent to an AI provider.
- **Demo-safe server key.** If you set a key on the server, each visitor gets a limited number of AI answers (`MEDRAG_MAX_AI_ANSWERS`, default 15), then falls back to free mode.

**MedRAG is a reference support tool for clinicians. It is not a substitute for clinical judgment**, and the app says so on every screen.

## How it works

1. **Read** each PDF page by page (pypdf).
2. **Split** each page into passages at sentence boundaries (~800 characters, one sentence of overlap). Passages never cross pages, so every one has a page number.
3. **Embed** passages locally with `all-MiniLM-L6-v2` and search by cosine similarity (FAISS when installed, numpy otherwise).
4. **Filter** out weak matches (similarity below 0.30) so off-topic questions get "not in your documents".
5. **Answer**: free mode quotes the passages; AI mode writes an answer that must cite numbered passages, and only those are shown as sources.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | [Streamlit](https://streamlit.io) | Fast to build, fast to run, no frontend build step |
| PDF extraction | pypdf | Page-by-page text extraction, maintained successor to PyPDF2 |
| Embeddings | [sentence-transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`) | Free, local, no API key, fast enough for interactive use |
| Vector search | [FAISS](https://github.com/facebookresearch/faiss) (cosine, in-memory) with a numpy fallback | Exact search, no external service |
| Generation | OpenAI `gpt-4o-mini` or Claude `claude-haiku-4-5` (optional) | Only used with a key; otherwise the app returns the relevant passages directly |

## Quickstart

```bash
./run.sh
```

This creates a virtual environment, installs dependencies, and launches the app at `http://localhost:8501`.

To test the retrieval pipeline on its own (no Streamlit, no PDFs needed):

```bash
python demo.py          # needs the embedding model
pytest -q tests         # offline tests, no model download needed
```

To deploy to a fresh GitHub repo:

```bash
./deploy.sh my-medrag-repo private
```

## Project layout

```
app.py           Streamlit UI
rag.py           Extraction, chunking, search, answers (no Streamlit)
demo.py          Standalone pipeline smoke test
samples/         Sample document for the one-click demo
tests/           Offline tests (run in GitHub Actions)
requirements.txt Python dependencies
run.sh           venv setup + launch
deploy.sh        git init + GitHub repo creation + push
PRD.md           Product requirements
```
