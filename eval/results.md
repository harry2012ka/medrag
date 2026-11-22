# MedRAG retrieval benchmark results

_Generated 2026-11-22 by `python eval/run_eval.py`. Embedding model: **all-MiniLM-L6-v2**. MIN_SCORE = 0.3, TOP_K = 4. Run in GitHub Actions ([eval run 45002493775](https://github.com/harry2012ka/medrag/actions/runs/45002493775)), Python 3.12, CPU torch._

69 questions over 4 synthetic documents in `eval/guidelines/`.

| Metric | Value |
|---|---|
| hit@1 (answerable, all types) | 87.3% |
| hit@3 (answerable, all types) | 96.4% |
| Correct refusal (unanswerable) | 64.3% |
| False refusal (answerable) | 0.0% |

## By question type

| Type | n | hit@1 | hit@3 | returned nothing |
|---|---|---|---|---|
| answerable | 24 | 100.0% | 100.0% | 0.0% |
| paraphrase | 18 | 77.8% | 94.4% | 0.0% |
| abbreviation | 13 | 76.9% | 92.3% | 0.0% |
| unanswerable | 14 | - | - | 64.3% |

## Relevance cutoff trade-off

| MIN_SCORE | hit@1 | hit@3 | false refusal | correct refusal |
|---|---|---|---|---|
| 0.15 | 87.3% | 96.4% | 0.0% | 21.4% |
| 0.20 | 87.3% | 96.4% | 0.0% | 35.7% |
| 0.25 | 87.3% | 96.4% | 0.0% | 57.1% |
| 0.30 (current) | 87.3% | 96.4% | 0.0% | 64.3% |
| 0.35 | 87.3% | 96.4% | 0.0% | 64.3% |
| 0.38 | 87.3% | 98.2% | 0.0% | 71.4% |
| 0.40 | 87.3% | 98.2% | 0.0% | 85.7% |
| 0.42 | 87.3% | 96.4% | 0.0% | 92.9% |
| 0.45 | 87.3% | 94.5% | 1.8% | 92.9% |
| 0.50 | 81.8% | 89.1% | 3.6% | 100.0% |

## Misses

- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got hypertension.txt p.4, hypertension.txt p.1, hypertension.txt p.1, ckd.txt p.2
- [paraphrase] Which diabetes pills cause the most low sugar episodes?: wanted type2_diabetes.txt p.2; got type2_diabetes.txt p.3, type2_diabetes.txt p.1, type2_diabetes.txt p.2, ckd.txt p.2
- [paraphrase] Which diabetes drugs help people lose weight?: wanted type2_diabetes.txt p.3; got type2_diabetes.txt p.1, type2_diabetes.txt p.3, ckd.txt p.2
- [paraphrase] What should be checked when kidney function keeps getting worse?: wanted ckd.txt p.3; got ckd.txt p.4, ckd.txt p.3, ckd.txt p.2, ckd.txt p.1
- [abbreviation] BP target on treatment: wanted hypertension.txt p.3; got hypertension.txt p.4, hypertension.txt p.3, hypertension.txt p.1
- [abbreviation] metformin eGFR cutoff: wanted type2_diabetes.txt p.3; got ckd.txt p.4, ckd.txt p.1, ckd.txt p.2
- [abbreviation] SGLT2 or GLP-1 in T2DM with CKD: wanted type2_diabetes.txt p.3; got ckd.txt p.2, type2_diabetes.txt p.3
- [unanswerable] What is the warfarin dose for atrial fibrillation?: wanted nothing; got hypertension.txt p.3, type2_diabetes.txt p.4, type2_diabetes.txt p.2
- [unanswerable] What is the dose of amoxicillin for children with otitis media?: wanted nothing; got asthma.txt p.3, asthma.txt p.2
- [unanswerable] How is rheumatoid arthritis treated with methotrexate?: wanted nothing; got asthma.txt p.3
- [unanswerable] What is the treatment for COPD exacerbation with antibiotics?: wanted nothing; got asthma.txt p.3, asthma.txt p.2
- [unanswerable] Which antidepressant is first-line for major depression?: wanted nothing; got hypertension.txt p.3, hypertension.txt p.4
