# MedRAG

**Ask your clinical documents a question. Get an answer with the file and page it came from.**

**Demo: https://medrag-production-b839.up.railway.app (sample document built in)**. Click **Try the sample document**, or upload your own PDFs.

## The problem

Clinical teams keep protocols, guidelines, drug monographs and SOPs as PDFs. Finding the one paragraph you need means Ctrl-F through a dozen files. General chatbots don't have your documents and can give a confident wrong answer. In a clinical setting, an answer without a source is worse than no answer.

## Who it's for

- Clinicians who need fast, checkable answers from their own reference PDFs
- Clinic operations and compliance teams working from protocol documents
- Patients reading their own (de-identified) health documents, through patient mode

## Features

- **Page citations.** Every passage belongs to one page, and every answer shows `file · p. N` tags with the quoted passage one click away. With AI answers on, only the passages the answer actually cited are shown as sources.
- **Says "not in your documents."** If nothing passes the relevance cutoff, the app says so and doesn't answer from outside your sources.
- **Hybrid search with clinical abbreviations.** Meaning-based search (`all-MiniLM-L6-v2`) combined with BM25 keyword scoring, so exact drug names, lab names and numbers rank well. About 45 common abbreviations (HTN, eGFR, T2DM, SGLT2, NSAID...) are expanded before searching.
- **Free by default.** With no API key you get the exact matching passages and nothing leaves the server. Add an OpenAI (`gpt-4o-mini`) or Claude (`claude-haiku-4-5`) key for written answers, follow-up questions and per-document summaries.
- **Grounded-answer enforcement.** The AI is told to answer only from numbered passages and cite each statement. An AI answer that cites no valid passage isn't shown (you get the passages instead). Fake citation labels, links, images and raw HTML are stripped from AI text. Refusals become the standard "not in your documents" message. Summaries must cite pages and may not add advice.
- **Patient mode.** "Who's reading?" switches to plain language at about an 8th-grade level. Answers that talk about starting, stopping or changing a medicine are blocked and replaced with the source passages and a "ask your doctor or pharmacist" note.
- **Emergency notice.** Questions that sound like an emergency (chest pain, can't breathe, stroke signs, overdose, suicidal thoughts, some Spanish phrasings) get a 911 / 988 / Poison Control notice at the top of the answer.
- **PHI redaction (best effort).** Uploads need a "no patient identifiers" checkbox first. Pattern-based checks flag likely identifiers (SSNs, record numbers, birth dates, labeled names, phone numbers, emails, street addresses) and warn in the sidebar. Those patterns, and labeled names wherever they reappear, are replaced before any text is sent to an AI provider. When the server's shared demo key is in use, AI is turned off entirely for documents with flagged identifiers.
- **AI budget limits.** With a server-side key, AI calls are capped per browser session (`MEDRAG_MAX_AI_ANSWERS`, default 15), per IP per day (`MEDRAG_MAX_AI_PER_IP_DAY`, 40) and per server per hour (`MEDRAG_MAX_AI_PER_HOUR`, 200). Past a limit the app falls back to free mode. Uploads are capped too (`MEDRAG_MAX_DOCS`, 10 files; `MEDRAG_MAX_CHUNKS`, 5000 passages; 500 pages per PDF; 25 MB per file).
- **Safe with messy files.** Encrypted, scanned, empty or corrupted PDFs show a message in the sidebar instead of crashing.
- **Conversation download** as Markdown, with citations.

## Safety and limits

- **Not a medical device.** MedRAG is a reference tool. It doesn't diagnose, and it is not a substitute for clinical judgment.
- **Not for real PHI** unless the AI provider you connect is covered by a Business Associate Agreement (BAA) with you. Free mode keeps text on the server, but the server still holds uploaded files in memory for the session.
- **Redaction is best effort.** It is pattern-based and catches common formats, not every possible identifier. Use de-identified documents.
- **English only.** Search, abbreviations and safety checks are built for English text (the emergency check also knows a few Spanish phrases).
- No OCR: scanned or image-only PDFs are refused with a message.
- Nothing is stored between sessions: refreshing the page clears documents and chat.

## How it works

1. **Read** each PDF page by page with pypdf.
2. **Split** each page into passages at sentence boundaries (about 800 characters, one sentence of overlap). Passages never cross pages, so each has one page number.
3. **Search**: expand abbreviations, embed the question locally, score every passage by cosine similarity (FAISS, numpy fallback) plus a BM25 keyword boost. Passages under the cutoff (`MIN_SCORE = 0.30`) are dropped; a strong multi-word keyword match may sit slightly under it. Up to 4 passages are kept, minus any much weaker than the best.
4. **Answer**: free mode quotes the passages. AI mode sends redacted passages to the provider, then enforces the citation rules above.

## How accuracy is measured

`eval/` holds a retrieval benchmark: 4 synthetic guideline documents (hypertension, type 2 diabetes, CKD, asthma) and 69 questions labeled with the correct file and page. Questions are split into four types: worded like the document, paraphrased, abbreviation-heavy, and unanswerable (should return nothing).

```bash
python eval/run_eval.py                    # writes eval/results.md
python eval/run_eval.py --threshold-sweep  # also shows the cutoff trade-off
```

It reports hit@1 and hit@3 (correct page ranked first / in the top 3), correct-refusal rate on unanswerable questions, false-refusal rate on answerable ones, and a per-type breakdown. It uses the real embedding model when installed. Otherwise it falls back to the offline test model with a warning, and those numbers check the pipeline, not real-world accuracy. See [eval/results.md](eval/results.md) for the latest run.

## Tech stack

| Layer | Choice |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| PDF extraction | pypdf |
| Embeddings | [sentence-transformers](https://www.sbert.net/) `all-MiniLM-L6-v2`, local, no key |
| Search | FAISS (cosine, in-memory) with numpy fallback, plus BM25 keyword scoring |
| Generation (optional) | OpenAI `gpt-4o-mini` or Claude `claude-haiku-4-5` |

## Run it

```bash
./run.sh                 # venv + install + launch at http://localhost:8501
python demo.py           # pipeline check without Streamlit (needs the embedding model)
pytest -q tests          # offline tests, no model download or network needed
```

To give visitors AI answers without their own key, set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` on the server (environment or `.streamlit/secrets.toml`). The budget limits above then apply.

## Deploy

**Docker (used for the live demo on Railway):** the `Dockerfile` installs CPU-only PyTorch, bakes the embedding model into the image so the first visitor doesn't wait, runs as a non-root user, and listens on `$PORT` (default 8080).

```bash
docker build -t medrag . && docker run -p 8080:8080 medrag
```

`Procfile` covers Heroku-style hosts. `./deploy.sh <repo-name> <public|private>` creates a GitHub repo and pushes.

## Tests

`tests/` runs offline in GitHub Actions on every push. A small word-hashing model stands in for sentence-transformers, so the tests cover extraction, chunking, search cutoffs, citations, grounded-answer checks, redaction, patient mode, emergency detection and the eval harness.

## Project layout

```
app.py            Streamlit UI, upload handling, AI budget limits
rag.py            Extraction, chunking, search, safety checks, answers (no Streamlit)
demo.py           Standalone pipeline check
samples/          Sample document for the one-click demo
eval/             Accuracy benchmark: synthetic guidelines, questions, runner, results
tests/            Offline tests
Dockerfile        Container for Railway or any Docker host
run.sh, deploy.sh Local launch, GitHub repo creation
PRD.md            Product requirements
```
