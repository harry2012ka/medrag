# MedRAG

**Ask your clinical PDFs a question. Get an answer quoted from your documents, with the file and page, or a plain "that's not in your documents."**

**Live demo: https://medrag-production-b839.up.railway.app**. Tap **Try the sample document**, then ask a question. No sign-up and no key needed.

[![tests](https://github.com/harry2012ka/medrag/actions/workflows/tests.yml/badge.svg)](https://github.com/harry2012ka/medrag/actions/workflows/tests.yml) [![eval](https://github.com/harry2012ka/medrag/actions/workflows/eval.yml/badge.svg)](https://github.com/harry2012ka/medrag/actions/workflows/eval.yml)

## Why not just ChatGPT or NotebookLM?

General chatbots, and even document tools like NotebookLM, are good at writing fluent answers. MedRAG is built around something narrower: **checkable answers, and a refusal when the documents don't cover the question.**

- **Free local mode.** With no API key, nothing leaves the server. Search runs on a small local model and you get the exact matching passages. No account and no per-question cost.
- **Grounded answers only.** With an AI key, the AI may only use the numbered passages it's given and must cite them. An answer that cites no real passage is thrown away and you get the passages instead. Only the passages actually cited are shown as sources.
- **Refuses when the documents don't cover it.** Passages below a relevance cutoff are dropped, so you get "not in your documents" instead of an answer from the model's general knowledge. (It reliably catches clearly off-topic questions but often misses nearby-topic ones; see the numbers below.)
- **Clinical guardrails built in.** Best-effort PHI redaction before anything goes to an AI provider, a 911 / 988 / Poison Control notice for emergency-sounding questions, and a patient mode that uses plain language and won't tell you to start, stop or change a medicine.

What it is **not**: it doesn't have NotebookLM's polish or writing quality, it isn't a medical device, and it hasn't been tested on real clinical documents at scale (see Limits).

## Accuracy (real model, measured in CI)

Retrieval benchmark: 214 hand-labeled questions over 9 synthetic guideline documents (hypertension, type 2 diabetes, CKD, asthma, anticoagulation, pediatric fever, COPD, depression, prenatal care). 72 of the questions are unanswerable, and most of those are hard negatives: same specialty, different drug or condition (enoxaparin dosing, croup, lithium, postpartum hemorrhage...). It runs with the same `all-MiniLM-L6-v2` model and search code as the live app. The [eval workflow](.github/workflows/eval.yml) re-runs it on every push to `master` and on PRs that touch search.

| Metric (MIN_SCORE 0.30) | Result |
|---|---|
| Right page ranked **first** (hit@1) | **74.6%** |
| Right page in the **top 3** (hit@3) | **90.1%** |
| Answerable questions wrongly refused | **2.8%** |
| Unanswerable questions correctly refused (search alone) | **34.7%** |

| Question type | n | hit@1 | hit@3 |
|---|---|---|---|
| Worded like the document | 58 | 87.9% | 100% |
| Paraphrased in plain words | 52 | 63.5% | 84.6% |
| Abbreviation-heavy ("NIV pH threshold AECOPD") | 32 | 68.8% | 81.2% |

**Finding the right page works. Knowing when not to answer doesn't, yet.** Search alone refuses only about 1 in 3 unanswerable questions. Clearly off-topic ones (tax filing, sourdough) are refused; same-specialty ones mostly aren't. Ask about enoxaparin dosing and you get the anticoagulation pages, because to this embedding model those questions look as close to the documents as real ones do. The unanswerable questions' best matches score up to 0.60, while some real answers score as low as 0.32, so no single cutoff separates them:

| MIN_SCORE | hit@3 | false refusal | correct refusal |
|---|---|---|---|
| **0.30 (current)** | 90.1% | 2.8% | 34.7% |
| 0.40 | 89.4% | 5.6% | 59.7% |
| 0.45 | 85.9% | 9.2% | 68.1% |
| 0.50 | 79.6% | 12.7% | 80.6% |

A separate "confidence floor" (refuse unless the best passage clears a higher bar) did no better than raising the cutoff. So the cutoff stays at 0.30, which favours showing the right page, and every answer shows its source and a match-strength note. In free mode a wrong-topic result is shown as quoted passages, not a written answer. In AI mode the model is told to say "not in your documents" when the passages don't answer the question; this benchmark doesn't measure that step. The likely real fix is an answerability check (a cross-encoder reranker or an LLM "does this passage answer the question?" pass), not a threshold.

An earlier, easier version of this benchmark (69 questions, 4 documents, few hard negatives) scored hit@3 96.4% and correct refusal 64.3%. The bigger set is the honest number. Full results, both sweeps and every miss: [eval/results.md](eval/results.md).

## Features

- **Page citations.** Every passage belongs to one page, and every answer shows `file · p. N` tags with the quoted passage one click away. With AI answers on, only the passages the answer actually cited are shown as sources.
- **Says "not in your documents."** If nothing passes the relevance cutoff, the app says so and doesn't answer from outside your sources. (Search alone misses many nearby-topic questions; see Accuracy.)
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
- **Weak at spotting unanswerable questions.** On same-specialty questions the documents don't cover, search alone refuses only about 1 in 3 (see Accuracy). Always read the cited passage.
- **Synthetic benchmark.** 214 questions over 9 synthetic documents, written by the same author as the questions. Good for catching regressions, not proof of accuracy on real hospital documents.
- No OCR: scanned or image-only PDFs are refused with a message.
- Nothing is stored between sessions: refreshing the page clears documents and chat.

## How it works

1. **Read** each PDF page by page with pypdf.
2. **Split** each page into passages at sentence boundaries (about 800 characters, one sentence of overlap). Passages never cross pages, so each has one page number.
3. **Search**: expand abbreviations, embed the question locally, score every passage by cosine similarity (FAISS, numpy fallback) plus a BM25 keyword boost. Passages under the cutoff (`MIN_SCORE = 0.30`) are dropped; a strong multi-word keyword match may sit slightly under it. Up to 4 passages are kept, minus any much weaker than the best.
4. **Answer**: free mode quotes the passages. AI mode sends redacted passages to the provider, then enforces the citation rules above.

## How accuracy is measured

`eval/` holds a retrieval benchmark: 9 synthetic guideline documents and 214 questions labeled with the correct file and page. Questions come in four types: worded like the document (58), paraphrased (52), abbreviation-heavy (32), and unanswerable (72, should return nothing; mostly same-specialty hard negatives plus some clearly off-topic ones).

It reports hit@1 and hit@3 (correct page ranked first / in the top 3), correct-refusal rate on unanswerable questions, false-refusal rate on answerable ones and a per-type breakdown. With `--threshold-sweep` it also reports the same numbers at other `MIN_SCORE` values and with a confidence floor.

**Real numbers come from CI.** The [`eval` workflow](.github/workflows/eval.yml) installs CPU PyTorch and the full requirements, then runs the benchmark with the real `all-MiniLM-L6-v2` model; `--require-real` makes it fail rather than fall back to the test model. It writes the summary table to the job page and uploads `eval/results.md` as an artifact. It runs on every push to `master`, on PRs that change search, the UI or the eval set, and by hand (workflow_dispatch). The numbers above are from [run 45003149788](https://github.com/harry2012ka/medrag/actions/runs/45003149788).

How the questions were written: the documents came first. The questions were then written from a list of page topics, not from the document text, in the words a clinician or patient would use, and the correct page was labelled afterwards. That reduces copying the documents' own wording, but the same author still wrote both, so treat the numbers as a regression check, not proof of accuracy on real clinical PDFs.

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
