# PRD — MedRAG

## Problem statement

Clinical staff and clinic operations teams need fast, trustworthy answers from their own reference documents (protocols, guidelines, drug monographs, SOPs). Manual search (Ctrl-F across PDFs) is slow and error-prone; general-purpose LLM chatbots don't have access to these private documents and can hallucinate confident-sounding but incorrect answers. In a clinical context, an answer without a verifiable source is a liability, not a convenience.

## Goals

- Let a user upload one or more PDFs and ask natural-language questions about their contents.
- Ground every answer in the user's actual documents via retrieval-augmented generation.
- Cite the exact source file and chunk for every answer, so the user can verify against the primary source.
- Work entirely free and local by default (no API key, no external calls) with an optional upgrade path to higher-quality generation via OpenAI.
- Never crash on malformed input (encrypted, scanned, or empty PDFs) — fail gracefully with a clear message.

## Non-goals

- Not a diagnostic tool and not a substitute for clinical judgment (explicitly disclaimed in-app).
- No persistent storage of documents or chat history across sessions/restarts — this is a stateless, in-memory tool per session.
- No multi-user auth, roles, or access control — single-user local/session tool.
- No OCR pipeline for scanned/image-only PDFs (out of scope; surfaced as an error instead).
- No support for non-PDF file formats in this version.
- No fine-tuning or custom model training.

## User stories

1. **As a clinician**, I want to upload a clinical guideline PDF and ask "What's the first-line treatment for X?" so I get an answer quickly without reading the whole document.
2. **As a clinic ops lead**, I want to upload several SOPs at once and see which ones are indexed and how many chunks each produced, so I trust the system has ingested everything.
3. **As any user**, I want every answer to show which file and chunk it came from, so I can pull up the original PDF and verify before acting on it.
4. **As a cost-conscious user**, I want to use the tool without ever entering an API key and still get useful, sourced answers.
5. **As a user with a better model available**, I want to optionally paste an OpenAI key to get more fluent, synthesized answers instead of raw passages.
6. **As a user who uploads a bad file** (encrypted, scanned, or corrupted), I want a clear error message in the sidebar instead of a crash, so I know what went wrong and can fix it.
7. **As a returning user in the same session**, I want to clear the chat or reset all documents independently, so I can start fresh without restarting the app.

## Functional requirements

- Multi-file PDF upload via sidebar.
- Text extraction with PyPDF2; chunking at ~800 characters with ~150-character overlap.
- Local embedding via `sentence-transformers` (`all-MiniLM-L6-v2`), cached per session so the model loads once.
- In-memory FAISS flat L2 index built incrementally as documents are processed.
- Chat interface with persistent history for the duration of the session.
- Retrieval of top-k relevant chunks per query; answer generation either via OpenAI (`gpt-4o-mini`, if a key is supplied) or direct passage return (fallback).
- Every answer displays citations: source filename + chunk index.
- On successful indexing, each document is automatically summarized in the chat (OpenAI if a key is present — including general lifestyle considerations and a physician-consultation reminder; a raw text preview otherwise).
- Sidebar shows: processing status, progress bar during ingestion, list of indexed documents with chunk counts, any processing errors.
- "Clear chat" button resets chat history only.
- "Reset all documents" button clears the index, chunk store, and document list.
- Persistent, visible disclaimer that the tool is reference support only, not a substitute for clinical judgment.

## Non-functional requirements

- **Reliability**: malformed PDFs (encrypted, image-only/no extractable text, corrupted, empty) must never crash the app — errors are caught and surfaced in the sidebar.
- **Cost**: default path (no OpenAI key) must incur zero API cost and require zero external network calls for inference.
- **Latency**: embedding and retrieval should feel interactive for documents in the tens-of-pages range on a standard laptop CPU.
- **Privacy**: documents are processed in memory only; nothing is written to disk or sent to a third party unless the user opts into OpenAI generation.
- **Portability**: runnable via a single `./run.sh` script with no manual environment setup.

## Risks

- **Hallucination risk in fallback-free mode is low** (raw passages returned), but when OpenAI generation is enabled, the model could still generate text not fully grounded in the retrieved context despite prompting — mitigated by requiring citations and instructing the model to say when context is insufficient, not eliminated entirely.
- **Scanned/image-only PDFs produce no text** — currently out of scope (no OCR), so those documents are unusable and only surfaced as an error, which may frustrate users who don't realize their PDF is a scanned image.
- **Embedding quality ceiling**: `all-MiniLM-L6-v2` is a small, general-purpose model — it may under-perform on dense clinical/medical terminology compared to a domain-tuned embedding model.
- **No persistence**: all indexed documents and chat history are lost on refresh/restart, which is by design but could surprise users expecting durability.
- **Single-session, single-user model**: `st.session_state` and an in-memory FAISS index don't scale to concurrent multi-user deployment without rearchitecting (per-user index isolation, persistent storage).
- **API key handling**: the OpenAI key is entered client-side into a password field and held in session state for the duration of the session — acceptable for local/single-user use, but not vetted for multi-tenant deployment.
