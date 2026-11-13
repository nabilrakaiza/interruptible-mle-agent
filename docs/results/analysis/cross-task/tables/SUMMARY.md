# Full plan analysis: spooky, insults, pizza (63 runs, C6 excluded)

Generated 8 Nov 2026 from `runs/_analysis/full_plan/runs/` (links to the 63 run folders) with the project's own scripts. Raw tables in the subfolders.

## Setup
- 21 runs per task: C1, C4, C5 seeds 0–4; A1-off, A4-off seeds 0–2. 4 hours each, DeepSeek V4 Flash 0731 (fp8), 2 CPUs.
- Spooky on the Mac (Docker); insults and pizza on Kaggle CPU (subprocess sandbox).

## 1. Outcomes (`outcomes/`)
- 63 of 63 runs valid and above the median.
- Medal rate (95% bootstrap over runs): C1 60% [33, 87], C4 47% [20, 73], C5 47% [20, 73], A1-off 44% [11, 78], A4-off 44% [11, 78]; C2 (oracle) 67%, C3 (top 3) 60%. All intervals overlap.
- Mean test score per task:

| Condition | Spooky ↓ | Insults ↑ | Pizza ↑ |
|---|---|---|---|
| C1 | 0.3290 | 0.9019 | **0.6978** |
| C2 (oracle) | 0.3284 | 0.9078 | 0.7037 |
| C3 (top 3) | 0.3288 | 0.9019 | 0.6983 |
| C4 | 0.3345 | 0.9054 | 0.6851 |
| C5 | **0.3133** | 0.9074 | 0.6847 |
| A1-off | 0.3592 | 0.9062 | 0.6851 |
| A4-off | 0.3424 | **0.9107** | 0.6818 |

## 2. Cost (`cost/`)
- About $21 for the 63 runs: $0.29–0.36 per run on average by condition (C1 $0.32, C4 $0.36, C5 $0.35, A1-off $0.29, A4-off $0.32).
- Mean nodes per run 77 (C1) to 90 (C4, C5); about 20–23k tokens per node.

## 3. Validation–test gap (`val_test_gap/`)
- Pick's test minus validation, oriented so negative = validation optimistic (median per task):

| Task | A1 on | A1 off |
|---|---|---|
| Spooky | −0.006 | −0.088 (worst −0.256, the seed-1 leak) |
| Insults | −0.001 | −0.015 |
| Pizza | −0.021 | −0.045 |

- Validation is more optimistic without A1 on every task. With A1, only pizza's gap is clearly non-zero (576 validation rows).
- Selection: the pick is a median 0.000 (spooky), 0.003 (insults), 0.009 (pizza) below the run's best node on test; worst 0.009 / 0.017 / 0.035 (A1 on).

## 4. Probe fidelity (`probe_fidelity/`)
- Rank correlation with test over each run's nodes (median over A1-on runs):

| Task | Probe vs test | Validation vs test | Probe top-5 overlap with test top-5 |
|---|---|---|---|
| Spooky (1,762 probe rows) | 0.97 | 0.98 | 0.8 |
| Insults (395) | 0.59 | 0.55 | 0.2 |
| Pizza (288) | 0.28 | 0.53 | 0.0 |

- The probe is as good as validation on spooky and insults, and much worse on pizza: the size of the held-out split decides whether its signal is usable.

## 5. Error taxonomy (`error_taxonomy/`)
- 5,381 nodes; 93.6–97.3% working per condition; timeouts 1.3–1.7%, runtime errors 0.7–2.6%, generation errors ≤0.8%, A1 leakage stops 3.
- 3,008 of 4,763 working improve nodes (63%) did not beat their parent; 158 changed nothing in the predictions.
- 111 working nodes (2.2%) labelled validation overfitting.

## 6. Findings (A4) accuracy (`finding_accuracy.csv`)
- 1,159 findings in the A1-on/A4-on runs; 1,007 claim helps or hurts.
- Supported by the cited validation scores: 61% (spooky 62%, insults 61%, pizza 60%). Unsupported mostly because the cited scores contradict the claimed effect (352 of 396).
- Replicated on the probe: spooky 50%, insults 25%, pizza 22% (81%, 40%, 36% of the supported ones).

## 7. Interventions
- Live C4 (15 runs): fired only on pizza (seeds 0 and 4, 3 prunes); the pick never changed.
- Live C5 (15 runs): 13 corrections (spooky 2, pizza 11, insults 0); never changed the pick. On pizza seeds 2–4, all 5 deleted findings that made a claim were right according to test.
- **Correction (13 Nov):** recounted from `replay/runs.csv`, the rule fires on 11 of the 48 non-C4 runs (pizza 8, spooky 3, insults 0): pick better on 3, unchanged within 0.0001 on 3, worse on 5. The original line follows.
- C4 rule replayed on the 48 non-C4 runs (`replay/`): fires on 10 (pizza 7, spooky 3, insults 0); pick better on 3 (spooky A1-off seed 1 +0.093, the leak; pizza A4-off s0 +0.006; pizza C5 s1 +0.003), unchanged on 2, worse on 5 (up to −0.024).

## 8. Other checks (see memory / `runs/_analysis/insults_complex/`, `runs/_analysis/mlebench_compare/`)
- Leakage: no script read outside its input; pizza's `giver_username_if_known` leaks the label (MLE-bench says to drop pizza); no pick used it.
- A1 split identical across seeds and conditions; A1-off gets validation rows as training data.
- Insults, complex models on the top-3 nodes' exact features: boosting worse on all 9 (LightGBM −0.005, XGBoost −0.009 test); ExtraTrees ≈ original.
- Other agents (MLE-bench grading reports): see `runs/_analysis/mlebench_compare/per_task.csv`.
