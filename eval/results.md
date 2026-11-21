# MedRAG retrieval benchmark results

_Generated 2026-11-21 by `python eval/run_eval.py`. Embedding model: **BagOfWordsModel (offline test stand-in)**. MIN_SCORE = 0.3, TOP_K = 4._

> **Offline stand-in model.** These numbers come from the word-hashing test model, not `all-MiniLM-L6-v2`. They check the pipeline, not real-world accuracy. Re-run with sentence-transformers installed for the numbers that match the live app.

69 questions over 4 synthetic documents in `eval/guidelines/`.

| Metric | Value |
|---|---|
| hit@1 (answerable, all types) | 54.5% |
| hit@3 (answerable, all types) | 56.4% |
| Correct refusal (unanswerable) | 100.0% |
| False refusal (answerable) | 29.1% |

## By question type

| Type | n | hit@1 | hit@3 | returned nothing |
|---|---|---|---|---|
| answerable | 24 | 75.0% | 75.0% | 25.0% |
| paraphrase | 18 | 27.8% | 27.8% | 44.4% |
| abbreviation | 13 | 53.8% | 61.5% | 15.4% |
| unanswerable | 14 | - | - | 100.0% |

## Relevance cutoff trade-off

| MIN_SCORE | hit@1 | hit@3 | false refusal | correct refusal |
|---|---|---|---|---|
| 0.15 | 74.5% | 81.8% | 0.0% | 42.9% |
| 0.20 | 70.9% | 76.4% | 1.8% | 71.4% |
| 0.25 | 69.1% | 72.7% | 9.1% | 85.7% |
| 0.30 (current) | 54.5% | 56.4% | 29.1% | 100.0% |
| 0.35 | 41.8% | 41.8% | 43.6% | 100.0% |
| 0.40 | 32.7% | 32.7% | 60.0% | 100.0% |
| 0.45 | 21.8% | 21.8% | 74.5% | 100.0% |
| 0.50 | 14.5% | 14.5% | 85.5% | 100.0% |

## Misses

- [answerable] How much dietary sodium is recommended for hypertension?: wanted hypertension.txt p.2; got nothing
- [answerable] What is resistant hypertension?: wanted hypertension.txt p.4; got nothing
- [answerable] What hemoglobin A1c range defines prediabetes?: wanted type2_diabetes.txt p.1; got nothing
- [answerable] How should hypoglycemia be treated?: wanted type2_diabetes.txt p.2; got nothing
- [answerable] What dose of oral prednisolone is used for a moderate asthma exacerbation?: wanted asthma.txt p.3; got nothing
- [answerable] What are the signs of a life-threatening asthma attack?: wanted asthma.txt p.3; got nothing
- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got hypertension.txt p.1
- [paraphrase] How much exercise per week helps bring blood pressure down?: wanted hypertension.txt p.2; got nothing
- [paraphrase] How many pills can a person be on before their blood pressure counts as hard to control?: wanted hypertension.txt p.4; got nothing
- [paraphrase] Which sugar test result means a person has diabetes?: wanted type2_diabetes.txt p.1; got nothing
- [paraphrase] What should someone do if their blood sugar drops too low?: wanted type2_diabetes.txt p.2; got nothing
- [paraphrase] Which diabetes pills cause the most low sugar episodes?: wanted type2_diabetes.txt p.2; got nothing
- [paraphrase] When does kidney function make it unsafe to keep taking metformin?: wanted type2_diabetes.txt p.3; got ckd.txt p.4
- [paraphrase] Which diabetes drugs help people lose weight?: wanted type2_diabetes.txt p.3; got nothing
- [paraphrase] How often should feet be checked in people with diabetes?: wanted type2_diabetes.txt p.4; got type2_diabetes.txt p.1
- [paraphrase] What should be checked when kidney function keeps getting worse?: wanted ckd.txt p.3; got ckd.txt p.4
- [paraphrase] What should a patient learn about before their kidneys fail?: wanted ckd.txt p.4; got nothing
- [paraphrase] Is it fine to use a rescue inhaler on its own without a steroid inhaler?: wanted asthma.txt p.2; got nothing
- [paraphrase] Which yearly vaccine is recommended for people with asthma?: wanted asthma.txt p.3; got asthma.txt p.2
- [abbreviation] BP target on treatment: wanted hypertension.txt p.3; got hypertension.txt p.4, hypertension.txt p.1
- [abbreviation] A1c cutoff for T2DM diagnosis: wanted type2_diabetes.txt p.1; got nothing
- [abbreviation] metformin eGFR cutoff: wanted type2_diabetes.txt p.3; got ckd.txt p.1
- [abbreviation] SGLT2 or GLP-1 in T2DM with CKD: wanted type2_diabetes.txt p.3; got type2_diabetes.txt p.1, ckd.txt p.2, type2_diabetes.txt p.3
- [abbreviation] statin for DM age 40 to 75: wanted type2_diabetes.txt p.4; got nothing
- [abbreviation] eGFR below 30 nephrology referral: wanted ckd.txt p.4; got ckd.txt p.1
