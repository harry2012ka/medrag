# MedRAG retrieval benchmark results

_Generated 2026-11-24 by `python eval/run_eval.py`. Embedding model: **all-MiniLM-L6-v2**. MIN_SCORE = 0.3, TOP_K = 4._

214 questions over 9 synthetic documents in `eval/guidelines/`.

| Metric | Value |
|---|---|
| hit@1 (answerable, all types) | 74.6% |
| hit@3 (answerable, all types) | 90.1% |
| Correct refusal (unanswerable) | 34.7% |
| False refusal (answerable) | 2.8% |

## By question type

| Type | n | hit@1 | hit@3 | returned nothing |
|---|---|---|---|---|
| answerable | 58 | 87.9% | 100.0% | 0.0% |
| paraphrase | 52 | 63.5% | 84.6% | 1.9% |
| abbreviation | 32 | 68.8% | 81.2% | 9.4% |
| unanswerable | 72 | - | - | 34.7% |

## Relevance cutoff trade-off

| MIN_SCORE | hit@1 | hit@3 | false refusal | correct refusal |
|---|---|---|---|---|
| 0.15 | 75.4% | 91.5% | 0.0% | 19.4% |
| 0.20 | 74.6% | 90.8% | 0.7% | 23.6% |
| 0.25 | 74.6% | 90.8% | 2.1% | 23.6% |
| 0.30 (current) | 74.6% | 90.1% | 2.8% | 34.7% |
| 0.35 | 73.9% | 89.4% | 4.9% | 47.2% |
| 0.38 | 73.9% | 89.4% | 4.9% | 55.6% |
| 0.40 | 73.9% | 89.4% | 5.6% | 59.7% |
| 0.42 | 73.2% | 88.0% | 6.3% | 61.1% |
| 0.45 | 72.5% | 85.9% | 9.2% | 68.1% |
| 0.50 | 67.6% | 79.6% | 12.7% | 80.6% |

## Confidence floor experiment

Same search, but refuse when the best passage's similarity is under the floor.

| MIN_SCORE | floor | hit@1 | hit@3 | false refusal | correct refusal |
|---|---|---|---|---|---|
| 0.30 | 0.40 | 73.2% | 88.0% | 7.0% | 59.7% |
| 0.30 | 0.42 | 71.8% | 86.6% | 9.2% | 63.9% |
| 0.30 | 0.45 | 69.7% | 83.8% | 12.0% | 70.8% |
| 0.30 | 0.48 | 67.6% | 81.0% | 14.8% | 79.2% |
| 0.30 | 0.50 | 64.8% | 77.5% | 18.3% | 83.3% |
| 0.35 | 0.40 | 73.2% | 88.0% | 7.0% | 59.7% |
| 0.35 | 0.42 | 71.8% | 86.6% | 9.2% | 63.9% |
| 0.35 | 0.45 | 69.7% | 83.8% | 12.0% | 70.8% |
| 0.35 | 0.48 | 67.6% | 81.0% | 14.8% | 79.2% |
| 0.35 | 0.50 | 64.8% | 77.5% | 18.3% | 83.3% |
| 0.38 | 0.40 | 73.2% | 88.7% | 7.0% | 59.7% |
| 0.38 | 0.42 | 71.8% | 86.6% | 9.2% | 63.9% |
| 0.38 | 0.45 | 69.7% | 83.8% | 12.0% | 70.8% |
| 0.38 | 0.48 | 67.6% | 81.0% | 14.8% | 79.2% |
| 0.38 | 0.50 | 64.8% | 77.5% | 18.3% | 83.3% |
| 0.40 | 0.42 | 71.8% | 86.6% | 9.2% | 63.9% |
| 0.40 | 0.45 | 69.7% | 83.8% | 12.0% | 70.8% |
| 0.40 | 0.48 | 67.6% | 81.0% | 14.8% | 79.2% |
| 0.40 | 0.50 | 64.8% | 77.5% | 18.3% | 83.3% |

## Misses

- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got hypertension.txt p.4, hypertension.txt p.1, hypertension.txt p.1, hypertension.txt p.3 (best similarity 0.41)
- [paraphrase] Which diabetes pills cause the most low sugar episodes?: wanted type2_diabetes.txt p.2; got type2_diabetes.txt p.3, type2_diabetes.txt p.1, type2_diabetes.txt p.2 (best similarity 0.51)
- [paraphrase] Which diabetes drugs help people lose weight?: wanted type2_diabetes.txt p.3; got type2_diabetes.txt p.1, type2_diabetes.txt p.3, ckd.txt p.2 (best similarity 0.57)
- [paraphrase] What should be checked when kidney function keeps getting worse?: wanted ckd.txt p.3; got ckd.txt p.4, ckd.txt p.3, ckd.txt p.2, anticoagulation.txt p.2 (best similarity 0.51)
- [paraphrase] Which yearly vaccine is recommended for people with asthma?: wanted asthma.txt p.3; got copd.txt p.2, asthma.txt p.3, prenatal_care.txt p.3 (best similarity 0.56)
- [abbreviation] BP target on treatment: wanted hypertension.txt p.3; got hypertension.txt p.4, hypertension.txt p.3, hypertension.txt p.1 (best similarity 0.54)
- [abbreviation] metformin eGFR cutoff: wanted type2_diabetes.txt p.3; got ckd.txt p.4, ckd.txt p.1, ckd.txt p.2 (best similarity 0.69)
- [abbreviation] SGLT2 or GLP-1 in T2DM with CKD: wanted type2_diabetes.txt p.3; got ckd.txt p.2, type2_diabetes.txt p.3 (best similarity 0.59)
- [unanswerable] How is acute appendicitis diagnosed?: wanted nothing; got pediatric_fever.txt p.2 (best similarity 0.39)
- [unanswerable] What antibiotic treats a urinary tract infection in pregnancy?: wanted nothing; got prenatal_care.txt p.1 (best similarity 0.34)
- [unanswerable] What is the dose of amoxicillin for children with otitis media?: wanted nothing; got pediatric_fever.txt p.3 (best similarity 0.53)
- [unanswerable] How should a migraine be treated in the emergency department?: wanted nothing; got pediatric_fever.txt p.3, prenatal_care.txt p.4 (best similarity 0.40)
- [unanswerable] What vaccines does a newborn baby need?: wanted nothing; got prenatal_care.txt p.3 (best similarity 0.60)
- [unanswerable] How is rheumatoid arthritis treated with methotrexate?: wanted nothing; got asthma.txt p.3, anticoagulation.txt p.2, anticoagulation.txt p.2 (best similarity 0.35)
- [unanswerable] What are the symptoms of Lyme disease?: wanted nothing; got pediatric_fever.txt p.2 (best similarity 0.33)
- [answerable] Which reversal agent is used for dabigatran?: wanted anticoagulation.txt p.4; got anticoagulation.txt p.2, anticoagulation.txt p.4, anticoagulation.txt p.2 (best similarity 0.55)
- [paraphrase] Why are the newer blood thinners usually chosen over warfarin for an irregular heartbeat?: wanted anticoagulation.txt p.2; got anticoagulation.txt p.3, anticoagulation.txt p.2, anticoagulation.txt p.4 (best similarity 0.55)
- [paraphrase] Do I have to stop eating spinach and salad if I'm on warfarin?: wanted anticoagulation.txt p.3; got anticoagulation.txt p.4, anticoagulation.txt p.3 (best similarity 0.44)
- [abbreviation] DOAC with mechanical valve OK?: wanted anticoagulation.txt p.2; got nothing
- [abbreviation] warfarin INR goal for DVT: wanted anticoagulation.txt p.3; got anticoagulation.txt p.1, anticoagulation.txt p.4, anticoagulation.txt p.3 (best similarity 0.61)
- [answerable] What workup does a febrile neonate under 28 days need?: wanted pediatric_fever.txt p.2; got pediatric_fever.txt p.4, pediatric_fever.txt p.2 (best similarity 0.46)
- [paraphrase] What signs mean a child with a temperature needs to be seen urgently?: wanted pediatric_fever.txt p.2; got pediatric_fever.txt p.1, pediatric_fever.txt p.2 (best similarity 0.61)
- [paraphrase] When should parents worry that a fever has gone on too long?: wanted pediatric_fever.txt p.4; got pediatric_fever.txt p.1 (best similarity 0.63)
- [answerable] When should an inhaled corticosteroid be added in COPD?: wanted copd.txt p.2; got copd.txt p.1, copd.txt p.2, copd.txt p.3 (best similarity 0.67)
- [answerable] What prednisone dose is used for a COPD exacerbation?: wanted copd.txt p.3; got copd.txt p.1, copd.txt p.3 (best similarity 0.67)
- [answerable] What oxygen saturation should be targeted in a COPD exacerbation?: wanted copd.txt p.3; got copd.txt p.4, copd.txt p.1, copd.txt p.3 (best similarity 0.71)
- [paraphrase] When does a chest flare-up in a smoker's lung disease need antibiotics?: wanted copd.txt p.3; got copd.txt p.1, copd.txt p.3, copd.txt p.4, asthma.txt p.3 (best similarity 0.54)
- [paraphrase] Why not just give lots of oxygen to someone with emphysema who is struggling to breathe?: wanted copd.txt p.3; got copd.txt p.4, copd.txt p.3 (best similarity 0.61)
- [paraphrase] What can help with breathlessness at the end stage of lung disease?: wanted copd.txt p.4; got copd.txt p.3, copd.txt p.1, copd.txt p.4, copd.txt p.2 (best similarity 0.62)
- [abbreviation] LAMA LABA initial COPD tx: wanted copd.txt p.2; got copd.txt p.1 (best similarity 0.58)
- [abbreviation] NIV pH threshold AECOPD: wanted copd.txt p.3; got nothing
- [abbreviation] roflumilast criteria COPD: wanted copd.txt p.4; got copd.txt p.1 (best similarity 0.72)
- [answerable] How long should antidepressants be continued after remission?: wanted depression.txt p.3; got depression.txt p.4, depression.txt p.3 (best similarity 0.68)
- [answerable] How should an antidepressant be stopped?: wanted depression.txt p.4; got depression.txt p.3, depression.txt p.4 (best similarity 0.69)
- [paraphrase] Are young adults at extra risk when they start antidepressants?: wanted depression.txt p.3; got depression.txt p.4 (best similarity 0.55)
- [paraphrase] When should a depressed patient be sent to a psychiatrist?: wanted depression.txt p.4; got depression.txt p.2, depression.txt p.3 (best similarity 0.54)
- [abbreviation] CBT for mild depression: wanted depression.txt p.3; got depression.txt p.1, depression.txt p.3 (best similarity 0.49)
- [paraphrase] How is the due date worked out?: wanted prenatal_care.txt p.1; got nothing
- [paraphrase] What shot does an Rh negative mom get and when?: wanted prenatal_care.txt p.2; got prenatal_care.txt p.3 (best similarity 0.33)
- [paraphrase] How much coffee is safe when pregnant?: wanted prenatal_care.txt p.3; got prenatal_care.txt p.1, prenatal_care.txt p.3 (best similarity 0.39)
- [paraphrase] How often are pregnancy checkups in the third trimester?: wanted prenatal_care.txt p.4; got prenatal_care.txt p.1, prenatal_care.txt p.3, prenatal_care.txt p.2 (best similarity 0.32)
- [paraphrase] What symptoms in pregnancy mean I should get help right away?: wanted prenatal_care.txt p.4; got prenatal_care.txt p.1, depression.txt p.4, depression.txt p.1 (best similarity 0.37)
- [abbreviation] cfDNA earliest GA: wanted prenatal_care.txt p.2; got nothing
- [unanswerable] What is the enoxaparin dose for treating a DVT?: wanted nothing; got anticoagulation.txt p.1, anticoagulation.txt p.2 (best similarity 0.58)
- [unanswerable] How is heparin-induced thrombocytopenia diagnosed?: wanted nothing; got anticoagulation.txt p.4, anticoagulation.txt p.1 (best similarity 0.44)
- [unanswerable] When is a left atrial appendage occlusion device considered?: wanted nothing; got anticoagulation.txt p.1, anticoagulation.txt p.4 (best similarity 0.35)
- [unanswerable] What dose of clopidogrel is used after a coronary stent?: wanted nothing; got anticoagulation.txt p.2, anticoagulation.txt p.3 (best similarity 0.53)
- [unanswerable] How is a superficial thrombophlebitis treated?: wanted nothing; got anticoagulation.txt p.1 (best similarity 0.51)
- [unanswerable] How long should dual antiplatelet therapy continue after a heart attack?: wanted nothing; got anticoagulation.txt p.1 (best similarity 0.56)
- [unanswerable] Should a patient with atrial fibrillation have cardioversion or rate control?: wanted nothing; got anticoagulation.txt p.1, anticoagulation.txt p.2 (best similarity 0.54)
- [unanswerable] What is the dose of amoxicillin for strep throat in children?: wanted nothing; got pediatric_fever.txt p.3 (best similarity 0.55)
- [unanswerable] How is croup treated?: wanted nothing; got anticoagulation.txt p.1, pediatric_fever.txt p.2 (best similarity 0.32)
- [unanswerable] At what age do babies get the measles vaccine?: wanted nothing; got prenatal_care.txt p.3 (best similarity 0.53)
- [unanswerable] How is bronchiolitis managed in infants?: wanted nothing; got copd.txt p.2, pediatric_fever.txt p.2, asthma.txt p.3, copd.txt p.3 (best similarity 0.43)
- [unanswerable] What causes a rash with fever in hand, foot and mouth disease?: wanted nothing; got pediatric_fever.txt p.4, pediatric_fever.txt p.2 (best similarity 0.42)
- [unanswerable] How much oral rehydration solution does a child with diarrhea need?: wanted nothing; got pediatric_fever.txt p.3, pediatric_fever.txt p.2, anticoagulation.txt p.2, pediatric_fever.txt p.1 (best similarity 0.46)
- [unanswerable] How is childhood ADHD diagnosed?: wanted nothing; got depression.txt p.1 (best similarity 0.31)
- [unanswerable] How is idiopathic pulmonary fibrosis treated?: wanted nothing; got copd.txt p.1, copd.txt p.2, anticoagulation.txt p.1, copd.txt p.3 (best similarity 0.47)
- [unanswerable] What is the treatment for community-acquired pneumonia in adults?: wanted nothing; got copd.txt p.2 (best similarity 0.58)
- [unanswerable] Which inhaler is used for cystic fibrosis?: wanted nothing; got asthma.txt p.2, copd.txt p.3 (best similarity 0.53)
- [unanswerable] How is obstructive sleep apnea diagnosed?: wanted nothing; got copd.txt p.1, asthma.txt p.1 (best similarity 0.43)
- [unanswerable] When is a lung cancer screening CT recommended?: wanted nothing; got copd.txt p.2, prenatal_care.txt p.2, depression.txt p.1, type2_diabetes.txt p.4 (best similarity 0.41)
- [unanswerable] What dose of varenicline helps people quit smoking?: wanted nothing; got copd.txt p.2, copd.txt p.4, depression.txt p.3, anticoagulation.txt p.3 (best similarity 0.46)
- [unanswerable] How is a spontaneous pneumothorax managed?: wanted nothing; got copd.txt p.3, copd.txt p.2, copd.txt p.1, copd.txt p.4 (best similarity 0.34)
- [unanswerable] How is generalized anxiety disorder treated?: wanted nothing; got depression.txt p.4, depression.txt p.3 (best similarity 0.44)
- [unanswerable] What is the starting dose of lithium for bipolar disorder?: wanted nothing; got depression.txt p.4, depression.txt p.3, anticoagulation.txt p.3, depression.txt p.2 (best similarity 0.49)
- [unanswerable] How is schizophrenia treated with antipsychotics?: wanted nothing; got depression.txt p.3 (best similarity 0.49)
- [unanswerable] What is the treatment for insomnia without medication?: wanted nothing; got depression.txt p.3, depression.txt p.4 (best similarity 0.46)
- [unanswerable] Which medicines treat PTSD?: wanted nothing; got depression.txt p.3, pediatric_fever.txt p.3, depression.txt p.2, depression.txt p.4 (best similarity 0.48)
- [unanswerable] How is ADHD in adults treated with stimulants?: wanted nothing; got depression.txt p.4, depression.txt p.3, hypertension.txt p.2, copd.txt p.2 (best similarity 0.43)
- [unanswerable] How is an ectopic pregnancy treated with methotrexate?: wanted nothing; got prenatal_care.txt p.1, anticoagulation.txt p.2, prenatal_care.txt p.2, pediatric_fever.txt p.3 (best similarity 0.32)
- [unanswerable] Which contraceptive is best after giving birth?: wanted nothing; got prenatal_care.txt p.1, depression.txt p.4, prenatal_care.txt p.3 (best similarity 0.34)
- [unanswerable] How is mastitis treated during breastfeeding?: wanted nothing; got depression.txt p.4, prenatal_care.txt p.3 (best similarity 0.37)
- [unanswerable] What is the dose of magnesium sulfate for eclampsia?: wanted nothing; got anticoagulation.txt p.2, pediatric_fever.txt p.3, prenatal_care.txt p.4, prenatal_care.txt p.1 (best similarity 0.50)
- [unanswerable] What is the target LDL for someone after a heart attack?: wanted nothing; got anticoagulation.txt p.3, hypertension.txt p.3, hypertension.txt p.4, type2_diabetes.txt p.3 (best similarity 0.34)
- [unanswerable] How is gout treated during a flare?: wanted nothing; got copd.txt p.3 (best similarity 0.30)
- [unanswerable] What is the first-line treatment for hypothyroidism?: wanted nothing; got hypertension.txt p.3, depression.txt p.3 (best similarity 0.34)
- [unanswerable] How is iron deficiency anemia treated?: wanted nothing; got ckd.txt p.3 (best similarity 0.39)
- [unanswerable] What dose of insulin should type 1 diabetes start on?: wanted nothing; got type2_diabetes.txt p.1, type2_diabetes.txt p.4 (best similarity 0.53)
- [unanswerable] How is heart failure with reduced ejection fraction treated?: wanted nothing; got ckd.txt p.4, type2_diabetes.txt p.3, copd.txt p.4, ckd.txt p.2 (best similarity 0.47)
- [unanswerable] How is a peptic ulcer from H. pylori treated?: wanted nothing; got pediatric_fever.txt p.3 (best similarity 0.32)
- [unanswerable] What is the treatment for shingles?: wanted nothing; got pediatric_fever.txt p.4, pediatric_fever.txt p.3 (best similarity 0.37)
- [unanswerable] What antibiotics treat cellulitis?: wanted nothing; got pediatric_fever.txt p.3 (best similarity 0.35)

## Answerability gate (cross-encoder reranker)

Top 8 hybrid passages (at the given MIN_SCORE) are re-scored by the cross-encoder; passages under RERANK_MIN are dropped. Adoption bar: correct refusal >= 70.0%, false refusal <= 5.0%, hit@3 >= 85.0%.

Latency is timed on 40 of the questions. Plain hybrid search latency: mean 7 ms, p95 8 ms per question (GitHub Actions CPU).

**cross-encoder/ms-marco-MiniLM-L-6-v2** (22.7M parameters, load 3.2 s, about +0 MB peak memory, activation Identity). Latency at MIN_SCORE 0.20, RERANK_MIN 0.1: mean 175 ms, p95 208 ms, max 215 ms; single CPU thread mean 332 ms, p95 395 ms.

| MIN_SCORE | RERANK_MIN | hit@1 | hit@3 | false refusal | correct refusal | meets bar |
|---|---|---|---|---|---|---|
| 0.20 | 0.01 | 84.5% | 88.7% | 9.2% | 72.2% | no |
| 0.20 | 0.02 | 82.4% | 85.9% | 12.0% | 75.0% | no |
| 0.20 | 0.05 | 81.7% | 83.8% | 13.4% | 79.2% | no |
| 0.20 | 0.1 **(best)** | 80.3% | 81.7% | 14.8% | 86.1% | no |
| 0.20 | 0.2 | 76.8% | 77.5% | 18.3% | 91.7% | no |
| 0.20 | 0.3 | 76.8% | 77.5% | 19.7% | 94.4% | no |
| 0.20 | 0.5 | 70.4% | 71.1% | 27.5% | 95.8% | no |
| 0.20 | 0.7 | 65.5% | 66.2% | 33.8% | 98.6% | no |
| 0.20 | 0.9 | 57.7% | 58.5% | 41.5% | 100.0% | no |
| 0.30 | 0.01 | 83.8% | 88.0% | 9.9% | 72.2% | no |
| 0.30 | 0.02 | 81.7% | 85.2% | 12.7% | 75.0% | no |
| 0.30 | 0.05 | 81.0% | 83.1% | 14.1% | 79.2% | no |
| 0.30 | 0.1 | 79.6% | 81.0% | 15.5% | 86.1% | no |
| 0.30 | 0.2 | 76.1% | 76.8% | 19.0% | 91.7% | no |
| 0.30 | 0.3 | 76.1% | 76.8% | 20.4% | 94.4% | no |
| 0.30 | 0.5 | 70.4% | 71.1% | 27.5% | 95.8% | no |
| 0.30 | 0.7 | 65.5% | 66.2% | 33.8% | 98.6% | no |
| 0.30 | 0.9 | 57.7% | 58.5% | 41.5% | 100.0% | no |

**cross-encoder/ms-marco-MiniLM-L-12-v2** (33.4M parameters, load 3.8 s, about +129 MB peak memory, activation Identity). Latency at MIN_SCORE 0.20, RERANK_MIN 0.05: mean 342 ms, p95 408 ms, max 426 ms; single CPU thread mean 664 ms, p95 786 ms.

| MIN_SCORE | RERANK_MIN | hit@1 | hit@3 | false refusal | correct refusal | meets bar |
|---|---|---|---|---|---|---|
| 0.20 | 0.01 | 83.8% | 88.0% | 9.2% | 69.4% | no |
| 0.20 | 0.02 | 83.8% | 88.0% | 9.9% | 72.2% | no |
| 0.20 | 0.05 **(best)** | 82.4% | 85.2% | 12.0% | 80.6% | no |
| 0.20 | 0.1 | 81.7% | 83.8% | 13.4% | 81.9% | no |
| 0.20 | 0.2 | 79.6% | 80.3% | 15.5% | 86.1% | no |
| 0.20 | 0.3 | 77.5% | 78.2% | 19.0% | 91.7% | no |
| 0.20 | 0.5 | 72.5% | 73.2% | 25.4% | 94.4% | no |
| 0.20 | 0.7 | 68.3% | 69.0% | 30.3% | 98.6% | no |
| 0.20 | 0.9 | 62.7% | 63.4% | 36.6% | 100.0% | no |
| 0.30 | 0.01 | 83.1% | 87.3% | 9.9% | 69.4% | no |
| 0.30 | 0.02 | 83.1% | 87.3% | 10.6% | 72.2% | no |
| 0.30 | 0.05 | 81.7% | 84.5% | 12.7% | 80.6% | no |
| 0.30 | 0.1 | 81.0% | 83.1% | 14.1% | 81.9% | no |
| 0.30 | 0.2 | 78.9% | 79.6% | 16.2% | 86.1% | no |
| 0.30 | 0.3 | 76.8% | 77.5% | 19.7% | 91.7% | no |
| 0.30 | 0.5 | 72.5% | 73.2% | 25.4% | 94.4% | no |
| 0.30 | 0.7 | 68.3% | 69.0% | 30.3% | 98.6% | no |
| 0.30 | 0.9 | 62.7% | 63.4% | 36.6% | 100.0% | no |

**ncbi/MedCPT-Cross-Encoder** (109.5M parameters, load 5.5 s, about +419 MB peak memory, activation Sigmoid). Latency at MIN_SCORE 0.20, RERANK_MIN 0.02: mean 1046 ms, p95 1231 ms, max 1290 ms; single CPU thread mean 2049 ms, p95 2424 ms.

| MIN_SCORE | RERANK_MIN | hit@1 | hit@3 | false refusal | correct refusal | meets bar |
|---|---|---|---|---|---|---|
| 0.20 | 0.01 | 86.6% | 93.7% | 4.9% | 83.3% | yes |
| 0.20 | 0.02 **(best)** | 86.6% | 93.0% | 4.9% | 87.5% | yes |
| 0.20 | 0.05 | 85.9% | 91.5% | 6.3% | 87.5% | no |
| 0.20 | 0.1 | 85.2% | 90.8% | 7.7% | 88.9% | no |
| 0.20 | 0.2 | 82.4% | 88.0% | 10.6% | 88.9% | no |
| 0.20 | 0.3 | 82.4% | 88.0% | 11.3% | 88.9% | no |
| 0.20 | 0.5 | 82.4% | 87.3% | 11.3% | 90.3% | no |
| 0.20 | 0.7 | 82.4% | 87.3% | 12.0% | 94.4% | no |
| 0.20 | 0.9 | 81.0% | 85.2% | 14.1% | 95.8% | no |
| 0.30 | 0.01 | 85.9% | 92.3% | 5.6% | 88.9% | no |
| 0.30 | 0.02 | 85.9% | 91.5% | 5.6% | 91.7% | no |
| 0.30 | 0.05 | 85.2% | 90.1% | 7.0% | 91.7% | no |
| 0.30 | 0.1 | 84.5% | 89.4% | 8.5% | 91.7% | no |
| 0.30 | 0.2 | 81.7% | 86.6% | 11.3% | 91.7% | no |
| 0.30 | 0.3 | 81.7% | 86.6% | 12.0% | 91.7% | no |
| 0.30 | 0.5 | 81.7% | 85.9% | 12.0% | 93.1% | no |
| 0.30 | 0.7 | 81.7% | 85.9% | 12.7% | 97.2% | no |
| 0.30 | 0.9 | 80.3% | 83.8% | 14.8% | 98.6% | no |

**BAAI/bge-reranker-base** (278.0M parameters, load 59.5 s, about +766 MB peak memory, activation Sigmoid). Latency at MIN_SCORE 0.30, RERANK_MIN 0.01: mean 944 ms, p95 1488 ms, max 1545 ms; single CPU thread mean 1822 ms, p95 2865 ms.

| MIN_SCORE | RERANK_MIN | hit@1 | hit@3 | false refusal | correct refusal | meets bar |
|---|---|---|---|---|---|---|
| 0.20 | 0.01 | 86.6% | 93.7% | 4.9% | 47.2% | no |
| 0.20 | 0.02 | 85.2% | 91.5% | 6.3% | 51.4% | no |
| 0.20 | 0.05 | 83.1% | 86.6% | 9.2% | 61.1% | no |
| 0.20 | 0.1 | 78.9% | 81.7% | 15.5% | 70.8% | no |
| 0.20 | 0.2 | 75.4% | 78.2% | 20.4% | 77.8% | no |
| 0.20 | 0.3 | 71.8% | 73.9% | 24.6% | 83.3% | no |
| 0.20 | 0.5 | 66.9% | 67.6% | 30.3% | 86.1% | no |
| 0.20 | 0.7 | 57.0% | 57.7% | 41.5% | 91.7% | no |
| 0.20 | 0.9 | 45.8% | 45.8% | 54.2% | 95.8% | no |
| 0.30 | 0.01 **(best)** | 84.5% | 91.5% | 5.6% | 59.7% | no |
| 0.30 | 0.02 | 83.1% | 89.4% | 8.5% | 61.1% | no |
| 0.30 | 0.05 | 81.7% | 85.2% | 10.6% | 69.4% | no |
| 0.30 | 0.1 | 78.2% | 81.0% | 16.2% | 77.8% | no |
| 0.30 | 0.2 | 74.6% | 77.5% | 21.1% | 83.3% | no |
| 0.30 | 0.3 | 71.1% | 73.2% | 25.4% | 87.5% | no |
| 0.30 | 0.5 | 66.9% | 67.6% | 30.3% | 87.5% | no |
| 0.30 | 0.7 | 57.0% | 57.7% | 41.5% | 91.7% | no |
| 0.30 | 0.9 | 45.8% | 45.8% | 54.2% | 95.8% | no |


<details><summary>cross-encoder/ms-marco-MiniLM-L-6-v2 misses at MIN_SCORE 0.20, RERANK_MIN 0.1 (36)</summary>

- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got nothing
- [paraphrase] How many pills can a person be on before their blood pressure counts as hard to control?: wanted hypertension.txt p.4; got nothing
- [paraphrase] Which diabetes pills cause the most low sugar episodes?: wanted type2_diabetes.txt p.2; got nothing
- [abbreviation] HTN diagnosis threshold: wanted hypertension.txt p.1; got nothing
- [abbreviation] BP target on treatment: wanted hypertension.txt p.3; got hypertension.txt p.4 (rerank 0.369)
- [abbreviation] avoid NSAIDs in CKD: wanted ckd.txt p.2; got nothing
- [unanswerable] What vaccines does a newborn baby need?: wanted nothing; got prenatal_care.txt p.3 (rerank 0.850)
- [paraphrase] Do I have to stop eating spinach and salad if I'm on warfarin?: wanted anticoagulation.txt p.3; got nothing
- [abbreviation] DOAC with mechanical valve OK?: wanted anticoagulation.txt p.2; got nothing
- [answerable] What workup does a febrile neonate under 28 days need?: wanted pediatric_fever.txt p.2; got nothing
- [paraphrase] What is the most helpful thing a smoker with emphysema can do?: wanted copd.txt p.2; got nothing
- [paraphrase] Which shots should people with chronic lung disease from smoking get?: wanted copd.txt p.2; got copd.txt p.1 (rerank 0.567)
- [paraphrase] When does a chest flare-up in a smoker's lung disease need antibiotics?: wanted copd.txt p.3; got nothing
- [paraphrase] Why not just give lots of oxygen to someone with emphysema who is struggling to breathe?: wanted copd.txt p.3; got nothing
- [paraphrase] What can help with breathlessness at the end stage of lung disease?: wanted copd.txt p.4; got copd.txt p.3 (rerank 0.320)
- [abbreviation] LAMA LABA initial COPD tx: wanted copd.txt p.2; got nothing
- [abbreviation] NIV pH threshold AECOPD: wanted copd.txt p.3; got nothing
- [paraphrase] What number can someone call or text if they are thinking about ending their life?: wanted depression.txt p.2; got nothing
- [paraphrase] My antidepressant isn't working after a month, what happens next?: wanted depression.txt p.3; got nothing
- [paraphrase] Are young adults at extra risk when they start antidepressants?: wanted depression.txt p.3; got depression.txt p.4 (rerank 0.286)
- [paraphrase] When should a depressed patient be sent to a psychiatrist?: wanted depression.txt p.4; got nothing
- [abbreviation] SSRI first line MDD: wanted depression.txt p.3; got hypertension.txt p.3 (rerank 0.645)
- [paraphrase] How is the due date worked out?: wanted prenatal_care.txt p.1; got nothing
- [paraphrase] How much coffee is safe when pregnant?: wanted prenatal_care.txt p.3; got nothing
- [paraphrase] How often are pregnancy checkups in the third trimester?: wanted prenatal_care.txt p.4; got nothing
- [paraphrase] What symptoms in pregnancy mean I should get help right away?: wanted prenatal_care.txt p.4; got nothing
- [abbreviation] cfDNA earliest GA: wanted prenatal_care.txt p.2; got nothing
- [unanswerable] What is the enoxaparin dose for treating a DVT?: wanted nothing; got anticoagulation.txt p.2 (rerank 0.155)
- [unanswerable] How is a superficial thrombophlebitis treated?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.583)
- [unanswerable] How long should dual antiplatelet therapy continue after a heart attack?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.678)
- [unanswerable] What is the dose of amoxicillin for strep throat in children?: wanted nothing; got pediatric_fever.txt p.3 (rerank 0.217)
- [unanswerable] What dose of varenicline helps people quit smoking?: wanted nothing; got copd.txt p.2 (rerank 0.223)
- [unanswerable] Which medicines treat PTSD?: wanted nothing; got depression.txt p.3 (rerank 0.153)
- [unanswerable] What is the dose of magnesium sulfate for eclampsia?: wanted nothing; got prenatal_care.txt p.4 (rerank 0.170)
- [unanswerable] What is the first-line treatment for hypothyroidism?: wanted nothing; got hypertension.txt p.3 (rerank 0.340)
- [unanswerable] What dose of insulin should type 1 diabetes start on?: wanted nothing; got type2_diabetes.txt p.1 (rerank 0.104)

</details>

<details><summary>cross-encoder/ms-marco-MiniLM-L-12-v2 misses at MIN_SCORE 0.20, RERANK_MIN 0.05 (35)</summary>

- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got nothing
- [paraphrase] How many pills can a person be on before their blood pressure counts as hard to control?: wanted hypertension.txt p.4; got nothing
- [paraphrase] Which diabetes pills cause the most low sugar episodes?: wanted type2_diabetes.txt p.2; got nothing
- [abbreviation] HTN diagnosis threshold: wanted hypertension.txt p.1; got nothing
- [abbreviation] avoid NSAIDs in CKD: wanted ckd.txt p.2; got nothing
- [unanswerable] What is the dose of amoxicillin for children with otitis media?: wanted nothing; got pediatric_fever.txt p.3 (rerank 0.195)
- [unanswerable] What vaccines does a newborn baby need?: wanted nothing; got prenatal_care.txt p.3 (rerank 0.865)
- [paraphrase] Do I have to stop eating spinach and salad if I'm on warfarin?: wanted anticoagulation.txt p.3; got nothing
- [abbreviation] DOAC with mechanical valve OK?: wanted anticoagulation.txt p.2; got nothing
- [paraphrase] What is the most helpful thing a smoker with emphysema can do?: wanted copd.txt p.2; got nothing
- [paraphrase] When does a chest flare-up in a smoker's lung disease need antibiotics?: wanted copd.txt p.3; got nothing
- [paraphrase] Why not just give lots of oxygen to someone with emphysema who is struggling to breathe?: wanted copd.txt p.3; got nothing
- [paraphrase] What can help with breathlessness at the end stage of lung disease?: wanted copd.txt p.4; got copd.txt p.3, copd.txt p.2 (rerank 0.275)
- [abbreviation] LAMA LABA initial COPD tx: wanted copd.txt p.2; got nothing
- [abbreviation] NIV pH threshold AECOPD: wanted copd.txt p.3; got nothing
- [paraphrase] What number can someone call or text if they are thinking about ending their life?: wanted depression.txt p.2; got nothing
- [paraphrase] My antidepressant isn't working after a month, what happens next?: wanted depression.txt p.3; got depression.txt p.4 (rerank 0.060)
- [paraphrase] Are young adults at extra risk when they start antidepressants?: wanted depression.txt p.3; got depression.txt p.4 (rerank 0.343)
- [paraphrase] When should a depressed patient be sent to a psychiatrist?: wanted depression.txt p.4; got nothing
- [abbreviation] SSRI first line MDD: wanted depression.txt p.3; got hypertension.txt p.3 (rerank 0.718)
- [paraphrase] How is the due date worked out?: wanted prenatal_care.txt p.1; got nothing
- [paraphrase] How often are pregnancy checkups in the third trimester?: wanted prenatal_care.txt p.4; got nothing
- [abbreviation] cfDNA earliest GA: wanted prenatal_care.txt p.2; got nothing
- [unanswerable] What is the enoxaparin dose for treating a DVT?: wanted nothing; got anticoagulation.txt p.2, anticoagulation.txt p.3 (rerank 0.404)
- [unanswerable] What dose of clopidogrel is used after a coronary stent?: wanted nothing; got anticoagulation.txt p.2 (rerank 0.116)
- [unanswerable] How is a superficial thrombophlebitis treated?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.288)
- [unanswerable] How long should dual antiplatelet therapy continue after a heart attack?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.650)
- [unanswerable] What is the dose of amoxicillin for strep throat in children?: wanted nothing; got pediatric_fever.txt p.3 (rerank 0.291)
- [unanswerable] What is the treatment for community-acquired pneumonia in adults?: wanted nothing; got copd.txt p.2 (rerank 0.217)
- [unanswerable] How is obstructive sleep apnea diagnosed?: wanted nothing; got copd.txt p.1 (rerank 0.098)
- [unanswerable] What dose of varenicline helps people quit smoking?: wanted nothing; got copd.txt p.2 (rerank 0.627)
- [unanswerable] Which medicines treat PTSD?: wanted nothing; got depression.txt p.3 (rerank 0.156)
- [unanswerable] What is the dose of magnesium sulfate for eclampsia?: wanted nothing; got prenatal_care.txt p.4 (rerank 0.244)
- [unanswerable] What is the first-line treatment for hypothyroidism?: wanted nothing; got hypertension.txt p.3 (rerank 0.542)
- [unanswerable] What dose of insulin should type 1 diabetes start on?: wanted nothing; got type2_diabetes.txt p.1 (rerank 0.464)

</details>

<details><summary>ncbi/MedCPT-Cross-Encoder misses at MIN_SCORE 0.20, RERANK_MIN 0.02 (19)</summary>

- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got hypertension.txt p.4 (rerank 0.275)
- [paraphrase] How many pills can a person be on before their blood pressure counts as hard to control?: wanted hypertension.txt p.4; got hypertension.txt p.2 (rerank 0.042)
- [paraphrase] Which diabetes pills cause the most low sugar episodes?: wanted type2_diabetes.txt p.2; got nothing
- [unanswerable] What vaccines does a newborn baby need?: wanted nothing; got prenatal_care.txt p.3 (rerank 0.984)
- [paraphrase] Why are the newer blood thinners usually chosen over warfarin for an irregular heartbeat?: wanted anticoagulation.txt p.2; got nothing
- [abbreviation] DOAC with mechanical valve OK?: wanted anticoagulation.txt p.2; got nothing
- [abbreviation] LAMA LABA initial COPD tx: wanted copd.txt p.2; got nothing
- [abbreviation] NIV pH threshold AECOPD: wanted copd.txt p.3; got nothing
- [paraphrase] When should a depressed patient be sent to a psychiatrist?: wanted depression.txt p.4; got depression.txt p.3, depression.txt p.2, depression.txt p.1, depression.txt p.4 (rerank 0.683)
- [paraphrase] How is the due date worked out?: wanted prenatal_care.txt p.1; got nothing
- [abbreviation] cfDNA earliest GA: wanted prenatal_care.txt p.2; got nothing
- [unanswerable] How is a superficial thrombophlebitis treated?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.788)
- [unanswerable] What causes a prolonged aPTT?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.058)
- [unanswerable] How long should dual antiplatelet therapy continue after a heart attack?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.580)
- [unanswerable] At what age do babies get the measles vaccine?: wanted nothing; got prenatal_care.txt p.3 (rerank 0.601)
- [unanswerable] What is the starting dose of lithium for bipolar disorder?: wanted nothing; got depression.txt p.4 (rerank 0.418)
- [unanswerable] What causes a miscarriage in the first trimester?: wanted nothing; got prenatal_care.txt p.1 (rerank 0.989)
- [unanswerable] When is labor induced for a pregnancy past the due date?: wanted nothing; got prenatal_care.txt p.1 (rerank 0.988)
- [unanswerable] What is the dose of magnesium sulfate for eclampsia?: wanted nothing; got prenatal_care.txt p.4 (rerank 0.616)

</details>

<details><summary>BAAI/bge-reranker-base misses at MIN_SCORE 0.30, RERANK_MIN 0.01 (41)</summary>

- [paraphrase] Is it okay to give both a pril and a sartan together for blood pressure?: wanted hypertension.txt p.3; got hypertension.txt p.4, prenatal_care.txt p.4, ckd.txt p.2, hypertension.txt p.2 (rerank 0.043)
- [abbreviation] BP target on treatment: wanted hypertension.txt p.3; got hypertension.txt p.4, hypertension.txt p.2, ckd.txt p.2, hypertension.txt p.3 (rerank 0.794)
- [unanswerable] What antibiotic treats a urinary tract infection in pregnancy?: wanted nothing; got prenatal_care.txt p.1, pediatric_fever.txt p.2 (rerank 0.193)
- [unanswerable] What is the dose of amoxicillin for children with otitis media?: wanted nothing; got anticoagulation.txt p.2, anticoagulation.txt p.3 (rerank 0.042)
- [unanswerable] What vaccines does a newborn baby need?: wanted nothing; got prenatal_care.txt p.3, pediatric_fever.txt p.2, copd.txt p.2, prenatal_care.txt p.2 (rerank 0.261)
- [unanswerable] What are the symptoms of Lyme disease?: wanted nothing; got pediatric_fever.txt p.2 (rerank 0.071)
- [abbreviation] DOAC with mechanical valve OK?: wanted anticoagulation.txt p.2; got nothing
- [paraphrase] Should I switch back and forth between Tylenol and Motrin for my kid's fever?: wanted pediatric_fever.txt p.3; got nothing
- [paraphrase] What is the most helpful thing a smoker with emphysema can do?: wanted copd.txt p.2; got nothing
- [paraphrase] Why not just give lots of oxygen to someone with emphysema who is struggling to breathe?: wanted copd.txt p.3; got nothing
- [abbreviation] LAMA LABA initial COPD tx: wanted copd.txt p.2; got nothing
- [abbreviation] NIV pH threshold AECOPD: wanted copd.txt p.3; got nothing
- [paraphrase] How is the due date worked out?: wanted prenatal_care.txt p.1; got nothing
- [paraphrase] What shot does an Rh negative mom get and when?: wanted prenatal_care.txt p.2; got prenatal_care.txt p.3 (rerank 0.012)
- [paraphrase] How often are pregnancy checkups in the third trimester?: wanted prenatal_care.txt p.4; got prenatal_care.txt p.1 (rerank 0.015)
- [abbreviation] cfDNA earliest GA: wanted prenatal_care.txt p.2; got nothing
- [unanswerable] What is the enoxaparin dose for treating a DVT?: wanted nothing; got anticoagulation.txt p.2, anticoagulation.txt p.1, hypertension.txt p.3, anticoagulation.txt p.3 (rerank 0.778)
- [unanswerable] How is heparin-induced thrombocytopenia diagnosed?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.701)
- [unanswerable] What dose of clopidogrel is used after a coronary stent?: wanted nothing; got anticoagulation.txt p.3, prenatal_care.txt p.1, anticoagulation.txt p.2 (rerank 0.048)
- [unanswerable] How is a superficial thrombophlebitis treated?: wanted nothing; got anticoagulation.txt p.1 (rerank 0.737)
- [unanswerable] How long should dual antiplatelet therapy continue after a heart attack?: wanted nothing; got anticoagulation.txt p.1, depression.txt p.3, anticoagulation.txt p.3 (rerank 0.670)
- [unanswerable] Should a patient with atrial fibrillation have cardioversion or rate control?: wanted nothing; got anticoagulation.txt p.3, anticoagulation.txt p.4, anticoagulation.txt p.1, anticoagulation.txt p.2 (rerank 0.079)
- [unanswerable] What is the dose of amoxicillin for strep throat in children?: wanted nothing; got anticoagulation.txt p.2, copd.txt p.3, anticoagulation.txt p.3, prenatal_care.txt p.1 (rerank 0.084)
- [unanswerable] At what age do babies get the measles vaccine?: wanted nothing; got prenatal_care.txt p.3, pediatric_fever.txt p.2 (rerank 0.065)
- [unanswerable] What causes a rash with fever in hand, foot and mouth disease?: wanted nothing; got pediatric_fever.txt p.2, pediatric_fever.txt p.4 (rerank 0.160)
- [unanswerable] How is idiopathic pulmonary fibrosis treated?: wanted nothing; got anticoagulation.txt p.1, copd.txt p.3, asthma.txt p.3 (rerank 0.608)
- [unanswerable] What is the treatment for community-acquired pneumonia in adults?: wanted nothing; got copd.txt p.2 (rerank 0.101)
- [unanswerable] Which inhaler is used for cystic fibrosis?: wanted nothing; got copd.txt p.3, asthma.txt p.2 (rerank 0.033)
- [unanswerable] What dose of varenicline helps people quit smoking?: wanted nothing; got anticoagulation.txt p.3, copd.txt p.2, anticoagulation.txt p.2, depression.txt p.4 (rerank 0.108)
- [unanswerable] How is generalized anxiety disorder treated?: wanted nothing; got depression.txt p.3 (rerank 0.973)
- [unanswerable] What is the starting dose of lithium for bipolar disorder?: wanted nothing; got depression.txt p.4, anticoagulation.txt p.3, prenatal_care.txt p.4 (rerank 0.244)
- [unanswerable] How is schizophrenia treated with antipsychotics?: wanted nothing; got depression.txt p.3 (rerank 0.594)
- [unanswerable] What is the treatment for insomnia without medication?: wanted nothing; got depression.txt p.4 (rerank 0.011)
- [unanswerable] Which medicines treat PTSD?: wanted nothing; got depression.txt p.3, depression.txt p.4, copd.txt p.2, depression.txt p.2 (rerank 0.981)
- [unanswerable] How is ADHD in adults treated with stimulants?: wanted nothing; got depression.txt p.3, hypertension.txt p.3 (rerank 0.939)
- [unanswerable] Which contraceptive is best after giving birth?: wanted nothing; got depression.txt p.4, prenatal_care.txt p.1 (rerank 0.074)
- [unanswerable] What is the dose of magnesium sulfate for eclampsia?: wanted nothing; got anticoagulation.txt p.2, anticoagulation.txt p.3, prenatal_care.txt p.4, prenatal_care.txt p.1 (rerank 0.067)
- [unanswerable] What is the target LDL for someone after a heart attack?: wanted nothing; got hypertension.txt p.3, hypertension.txt p.4, copd.txt p.3, anticoagulation.txt p.3 (rerank 0.043)
- [unanswerable] What is the first-line treatment for hypothyroidism?: wanted nothing; got hypertension.txt p.3 (rerank 0.209)
- [unanswerable] What dose of insulin should type 1 diabetes start on?: wanted nothing; got anticoagulation.txt p.2, type2_diabetes.txt p.1, anticoagulation.txt p.3 (rerank 0.027)
- [unanswerable] How is heart failure with reduced ejection fraction treated?: wanted nothing; got anticoagulation.txt p.3, type2_diabetes.txt p.3, copd.txt p.4 (rerank 0.045)

</details>
