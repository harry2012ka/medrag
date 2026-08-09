# MedRAG

Streamlit RAG app for clinical PDF Q&A.

## Stack
- Frontend: Streamlit (app.py)
- Embeddings: sentence-transformers, local, no API key needed by default
- Vector search: FAISS in-memory
- Optional OpenAI generation if user supplies a key

## Commands
- Run: ./run.sh
- Deploy: ./deploy.sh <repo-name> <public|private>
- Test pipeline only: python demo.py

## Conventions
- Keep the free/local path working without any API key — that's the core value prop
- Never crash on bad PDFs — surface errors in the sidebar
- Every answer must cite source file + chunk
