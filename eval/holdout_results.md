# MedRAG held-out results (2026-11-26)

_From the CI `eval` run with the real models (GitHub Actions run 45889986836)._

124 new questions, never used for tuning. Embedding model: all-MiniLM-L6-v2. Cutoffs frozen at the shipped values: MIN_SCORE 0.3, RERANK_HYBRID_MIN 0.2, RERANK_MIN 0.02.


**Search only (MIN_SCORE 0.3)**


| | value |
|---|---|
| right page first (hit@1) | 77.1% |
| right page in top 3 (hit@3) | 90.6% |
| answerable questions wrongly refused | 2.1% |
| unanswerable questions correctly refused | 3.6% |



| type | n | hit@3 | refused |
|---|---|---|---|
| answerable | 41 | 95.1% | 0.0% |
| paraphrase | 35 | 94.3% | 0.0% |
| abbreviation | 20 | 75.0% | 10.0% |
| unanswerable | 28 | 0.0% | 3.6% |



**With the answer checker ncbi/MedCPT-Cross-Encoder (what the live app runs)**


| | value |
|---|---|
| right page first (hit@1) | 92.7% |
| right page in top 3 (hit@3) | 95.8% |
| answerable questions wrongly refused | 4.2% |
| unanswerable questions correctly refused | 67.9% |



| type | n | hit@3 | refused |
|---|---|---|---|
| answerable | 41 | 100.0% | 0.0% |
| paraphrase | 35 | 88.6% | 11.4% |
| abbreviation | 20 | 100.0% | 0.0% |
| unanswerable | 28 | 0.0% | 67.9% |



<details><summary>13 misses with the answer checker</summary>

- missed (paraphrase): "Can a baby aspirin replace a blood thinner for stroke prevention in an irregular heartbeat?" wanted anticoagulation.txt p1, refused
- missed (paraphrase): "Which painkillers should people with weak kidneys stay away from?" wanted ckd.txt p2, refused
- missed (paraphrase): "Should I give my toddler Tylenol and Advil at the same time?" wanted pediatric_fever.txt p3, refused
- missed (paraphrase): "Which baby scan checks the baby's body parts in mid pregnancy?" wanted prenatal_care.txt p2, refused
- answered an unanswerable question: "What INR range is targeted for a mechanical aortic valve?" -> [('anticoagulation.txt', 3), ('anticoagulation.txt', 2)]
- answered an unanswerable question: "What is the edoxaban dose for atrial fibrillation?" -> [('anticoagulation.txt', 2), ('anticoagulation.txt', 4)]
- answered an unanswerable question: "What phosphate binder is preferred in kidney failure?" -> [('ckd.txt', 2)]
- answered an unanswerable question: "How often should hemodialysis sessions be scheduled?" -> [('anticoagulation.txt', 2)]
- answered an unanswerable question: "What blood pressure target applies to adults over 80?" -> [('hypertension.txt', 3), ('hypertension.txt', 1)]
- answered an unanswerable question: "What intravenous drug lowers blood pressure in a hypertensive emergency?" -> [('hypertension.txt', 4)]
- answered an unanswerable question: "What antibiotic treats a urinary tract infection in a child with fever?" -> [('pediatric_fever.txt', 2)]
- answered an unanswerable question: "What insulin regimen is started for type 1 diabetes?" -> [('type2_diabetes.txt', 3)]
- answered an unanswerable question: "Which continuous glucose monitor is best?" -> [('type2_diabetes.txt', 2)]

</details>

## What this means

On questions it was never tuned on, the shipped app still finds the right page in the top 3 for 96% of answerable questions and wrongly refuses about 4%. It correctly refuses only **68%** of questions the documents don't cover, versus 88% on the tuning set: the tuned number was about 20 points optimistic. Most misses are near-miss questions on a covered topic (an aortic-valve INR when only the mitral one is in the documents, edoxaban when only other anticoagulants are) where a related passage scores high enough to pass. Search alone refuses almost nothing (3.6%); the MedCPT answer checker does nearly all of the refusing.
