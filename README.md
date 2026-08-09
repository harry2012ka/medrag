# MedRAG

**Ask your clinical documents a question. Get an answer with the exact source and passage it came from.**

## 🎥 Demo

> _[Loom demo link — paste here]_

## The problem

Clinical teams sit on huge piles of PDFs — protocols, guidelines, drug monographs, internal SOPs — and finding the one paragraph you need means Ctrl-F-ing through a dozen documents, or worse, relying on memory. General-purpose chatbots either don't have your documents or will happily hallucinate an answer that sounds confident and is wrong. In a clinical setting, an unsourced answer is worse than no answer.

## Who it's for

- Clinicians and clinical staff who need fast, traceable answers from internal guidelines or reference PDFs
- Clinic operations and compliance teams standardizing on protocol documents
- Anyone who wants document Q&A that's private, cheap (or free), and shows its work

## What it does

MedRAG lets you upload one or more PDFs, then ask questions in a chat interface. Every answer is grounded in the actual text of your documents and **cites the exact source file and chunk** it was pulled from — so you can always go verify the primary source yourself.

- Upload multiple PDFs at once; watch them get processed in real time
- Automatically summarizes each document as soon as it's indexed — with an OpenAI key, the summary includes general lifestyle considerations and always closes with a reminder to consult a physician before acting on it
- Ask questions in natural language, get answers in a persistent chat thread
- Works completely free and offline-capable by default — no API key required
- Optionally add an OpenAI key for more fluent, synthesized answers (`gpt-4o-mini`)
- Every response is cited down to the source document and chunk
- Handles messy real-world PDFs (encrypted, scanned/image-only, empty) without crashing — errors surface clearly in the sidebar instead

**MedRAG is a reference support tool only. It is not a substitute for clinical judgment**, and this disclaimer is shown persistently in the app itself.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| UI | [Streamlit](https://streamlit.io) | Fast to build, fast to run, no frontend build step |
| PDF extraction | PyPDF2 | Simple, dependency-light text extraction |
| Embeddings | [sentence-transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`) | Free, local, no API key, fast enough for interactive use |
| Vector search | [FAISS](https://github.com/facebookresearch/faiss) (in-memory flat L2) | Simple, exact nearest-neighbor search, no external service |
| Generation | OpenAI `gpt-4o-mini` (optional) | Only used if you supply a key; otherwise the app returns the top retrieved passages directly |

## Quickstart

```bash
./run.sh
```

This creates a virtual environment, installs dependencies, and launches the app at `http://localhost:8501`.

To test the retrieval pipeline on its own (no Streamlit, no PDFs needed):

```bash
python demo.py
```

To deploy to a fresh GitHub repo:

```bash
./deploy.sh my-medrag-repo private
```

## Project layout

```
app.py           Streamlit app (UI + RAG pipeline)
demo.py          Standalone pipeline smoke test
requirements.txt Python dependencies
run.sh           venv setup + launch
deploy.sh        git init + GitHub repo creation + push
PRD.md           Product requirements
```
