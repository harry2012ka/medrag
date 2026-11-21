# MedRAG

Streamlit RAG app for clinical PDF Q&A.

## Stack
- Frontend: Streamlit (app.py); core logic in rag.py
- Embeddings: sentence-transformers, local, no API key needed by default
- PDF text: pypdf, page by page (citations are file + page)
- Search: hybrid, FAISS in-memory cosine (numpy fallback) + BM25 keywords + abbreviation expansion
- Optional OpenAI or Claude generation if a key is supplied (user's or server's, with budget limits)

## Commands
- Run: ./run.sh
- Deploy: ./deploy.sh <repo-name> <public|private>
- Test pipeline only: python demo.py
- Offline tests: pytest -q tests
- Accuracy benchmark: python eval/run_eval.py [--threshold-sweep] (writes eval/results.md)

## Conventions
- Keep the free/local path working without any API key — that's the core value prop
- Never crash on bad PDFs — surface errors in the sidebar
- Every answer must cite source file + page, and only the passages it used
- Never invent clinical advice; if the documents don't cover it, say so
- Summaries: document facts only, each cites its page, no added advice
- Re-run the eval after changing search, chunking or MIN_SCORE
