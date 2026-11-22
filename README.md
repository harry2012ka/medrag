# MedRAG

**Ask your clinical PDFs a question. Get an answer quoted from your documents, with the file and page, or a plain "that's not in your documents."**

**Live demo: https://medrag-production-b839.up.railway.app**. Tap **Try the sample document**, then ask a question. No sign-up and no key needed.

[![tests](https://github.com/harry2012ka/medrag/actions/workflows/tests.yml/badge.svg)](https://github.com/harry2012ka/medrag/actions/workflows/tests.yml) [![eval](https://github.com/harry2012ka/medrag/actions/workflows/eval.yml/badge.svg)](https://github.com/harry2012ka/medrag/actions/workflows/eval.yml)

## Why not just ChatGPT or NotebookLM?

General chatbots, and even document tools like NotebookLM, are good at writing fluent answers. MedRAG is built around something narrower: **checkable answers, and a refusal when the documents don't cover the question.**

- **Free local mode.** With no API key, nothing leaves the server. Search runs on a small local model and you get the exact matching passages. No account and no per-question cost.
- **Grounded answers only.** With an AI key, the AI may only use the numbered passages it's given and must cite them. An answer that cites no real passage is thrown away and you get the passages instead. Only the passages actually cited are shown as sources.
- **Refuses when the documents don't cover it.** Passages below a relevance cutoff are dropped, so you get "not in your documents" instead of an answer from the model's general knowledge. (This filter isn't perfect; see the numbers below.)
- **Clinical guardrails built in.** Best-effort PHI redaction before anything goes to an AI provider, a 911 / 988 / Poison Control notice for emergency-sounding questions, and a patient mode that uses plain language and won't tell you to start, stop or change a medicine.

What it is **not**: it doesn't have NotebookLM's polish or writing quality, it isn't a medical device, and it hasn't been tested on real clinical documents at scale (see Limits).

## Accuracy (real model, measured in CI)

Retrieval benchmark: 69 hand-labeled questions over 4 synthetic guideline documents, run with the same `all-MiniLM-L6-v2` model and search code as the live app. The [eval workflow](.github/workflows/eval.yml) re-runs it on every push to `master`.

| Metric | Result |
|---|---|
| Right page ranked **first** (hit@1) | **87.3%** |
| Right page in the **top 3** (hit@3) | **96.4%** |
| Answerable questions wrongly refused | **0%** |
| Off-topic questions correctly refused (search alone) | **64.3%** |

| Question type | n | hit@1 | hit@3 |
|---|---|---|---|
| Worded like the document | 24 | 100% | 100% |
| Paraphrased in plain words | 18 | 77.8% | 94.4% |
| Abbreviation-heavy ("metformin eGFR cutoff") | 13 | 76.9% | 92.3% |

**The weak spot is refusal.** About 1 in 3 off-topic questions (warfarin dosing, amoxicillin for ear infections, COPD antibiotics...) still pull up loosely related passages, likely because the test documents share a lot of drug vocabulary. In free mode the user then sees quoted passages with a match-strength note, not a written answer, but it is still a miss. The cutoff sweep below shows `MIN_SCORE = 0.40` would raise correct refusal to 85.7% with no new false refusals on this set. It isn't changed yet: at 0.42-0.45 right answers start dropping out, and 16 passages is too few to trust a cutoff that close to the edge without a bigger, more varied eval set.

"Correct refusal" is measured on search alone. In AI mode the model gets a second chance to say "not in your documents", which this benchmark doesn't measure. Full results, the cutoff trade-off and every miss: [eval/results.md](eval/results.md).

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

## Limits (read before relying on it)

- **Not a medical device.** MedRAG is a reference tool. It doesn't diagnose, and it is not a substitute for clinical judgment.
- **Not for real PHI** unless the AI provider you connect is covered by a Business Associate Agreement (BAA) with you. Free mode keeps text on the server, but the server still holds uploaded files in memory for the session.
- **Redaction is best effort.** It is pattern-based and catches common formats, not every possible identifier. Use de-identified documents.
- **English only.** Search, abbreviations and safety checks are built for English text (the emergency check also knows a few Spanish phrases).
- **Small benchmark.** The eval set is 69 questions over 16 passages that the same author wrote. That's enough to catch regressions and tune the cutoff, not to prove accuracy on real hospital documents.
- No OCR: scanned or image-only PDFs are refused with a message.
- Nothing is stored between sessions: refreshing the page clears documents and chat.

## How it works

1. **Read** each PDF page by page with pypdf.
2. **Split** each page into passages at sentence boundaries (about 800 characters, one sentence of overlap). Passages never cross pages, so each has one page number.
3. **Search**: expand abbreviations, embed the question locally, score every passage by cosine similarity (FAISS, numpy fallback) plus a BM25 keyword boost. Passages under the cutoff (`MIN_SCORE = 0.30`) are dropped; a strong multi-word keyword match may sit slightly under it. Up to 4 passages are kept, minus any much weaker than the best.
4. **Answer**: free mode quotes the passages. AI mode sends redacted passages to the provider, then enforces the citation rules above.

## How accuracy is measured

`eval/` holds a retrieval benchmark: 4 synthetic guideline documents (hypertension, type 2 diabetes, CKD, asthma; 16 passages in total) and 69 questions labeled with the correct file and page. Questions come in four types: worded like the document (24), paraphrased (18), abbreviation-heavy (13), and unanswerable (14, should return nothing).

It reports hit@1 and hit@3 (correct page ranked first / in the top 3), correct-refusal rate on unanswerable questions, false-refusal rate on answerable ones, a per-type breakdown, and with `--threshold-sweep` the same numbers at other `MIN_SCORE` values.

**Real numbers come from CI.** The [`eval` workflow](.github/workflows/eval.yml) installs CPU PyTorch and the full requirements, runs the benchmark with the real `all-MiniLM-L6-v2` model (`--require-real` makes it fail rather than fall back to the test model), writes the summary table to the job page, and uploads `eval/results.md` as an artifact. It runs on every push to `master` and can be started by hand (workflow_dispatch). The numbers above are from [run 45002493775](https://github.com/harry2012ka/medrag/actions/runs/45002493775) at `MIN_SCORE = 0.30`:

| MIN_SCORE | hit@1 | hit@3 | false refusal | correct refusal |
|---|---|---|---|---|
| 0.25 | 87.3% | 96.4% | 0.0% | 57.1% |
| **0.30 (current)** | 87.3% | 96.4% | 0.0% | 64.3% |
| 0.35 | 87.3% | 96.4% | 0.0% | 64.3% |
| 0.38 | 87.3% | 98.2% | 0.0% | 71.4% |
| 0.40 | 87.3% | 98.2% | 0.0% | 85.7% |
| 0.42 | 87.3% | 96.4% | 0.0% | 92.9% |
| 0.45 | 87.3% | 94.5% | 1.8% | 92.9% |
| 0.50 | 81.8% | 89.1% | 3.6% | 100.0% |

Locally:

```bash
python eval/run_eval.py                    # writes eval/results.md
python eval/run_eval.py --threshold-sweep  # also shows the cutoff trade-off
```

Without sentence-transformers installed it falls back to the offline test model with a warning; those numbers check the pipeline, not real-world accuracy.

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

`tests/` runs offline in GitHub Actions on every push (the `tests` workflow, a few seconds). `tests/test_app_smoke.py` clicks through the real Streamlit UI (empty state, sample document, a question with citations, an off-topic refusal); it is skipped without Streamlit installed and runs in the `eval` workflow. A small word-hashing model stands in for sentence-transformers, so the tests cover extraction, chunking, search cutoffs, citations, grounded-answer checks, redaction, patient mode, emergency detection and the eval harness.

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
