# Further analyses

> Exported 9 Nov 2026 from Nabil's analysis doc, [Full-plan results](https://claude.ai/artifact/1AHcCcSLLuLfqSGPkTFe5W), tab “Further analyses”. Charts are images of the doc's live charts. Paths under `runs/` are on Nabil's Mac; the data and scripts used are copied next to this file.

Picking the final node by validation is already the best simple rule, conditions do not differ across tasks, and spooky was still improving when its runs stopped. Four analyses on the 63 full-plan runs (8 Nov 2026); runs with A1 unless stated.

## 1. Other ways to pick the final node

No alternative rule beats picking by validation. Each rule picks one working node per run; “loss” is how far its test score is from the run's best node on test.

| Rule | Spooky test (loss) | Insults test (loss) | Pizza test (loss) |
| --- | --- | --- | --- |
| Best validation (the rule we use) | 0.3284 (0.0009) | 0.9059 (0.0039) | 0.6879 (0.0105) |
| Best probe | 0.3296 (0.0021) | 0.9057 (0.0041) | 0.6790 (0.0195) |
| Validation and probe averaged, weighted by rows | 0.3285 (0.0011) | 0.9060 (0.0038) | 0.6868 (0.0117) |
| Mean rank on validation and probe | 0.3286 (0.0012) | 0.9059 (0.0039) | 0.6840 (0.0145) |

Means over the 18 runs with A1 per task; spooky is log loss (lower is better), insults and pizza AUC.

- **Pizza:** picking by probe loses 0.009 of AUC against validation (worse on 12 runs, better on 6); combining the two is worse on 8 runs and better on 4. The 576 validation rows are noisy, but the 288 probe rows are noisier, and adding them does not help.
- **Spooky:** the combined rule changes the pick on only 4 of 18 runs; the probe alone is worse on 8.
- **Insults:** every rule is within 0.0003.
- **Recommendation:** keep picking by validation and keep the probe as a held-out check; using it for selection would also spend it.

## 2. When each run found its final pick

Spooky runs found their pick at the very end; pizza runs often found it early and spent the rest of the budget without beating it.

| Task | Pick found at (median share of the run's nodes) | Middle half of runs | Earliest |
| --- | --- | --- | --- |
| Spooky | 97% | 95% – 98% | 59% |
| Insults | 89% | 75% – 97% | 38% |
| Pizza | 84% | 69% – 96% | 14% |

Measured by node order, not wall clock: spooky seeds 0–2 were resumed days after their first 2 hours, so a time-based share would count that gap.

- **Spooky was still improving when the budget ran out:** half its runs found their pick in the last 3% of their nodes. This fits seeds 0–2 improving in 10 of 13 runs when resumed from 2 to 4 hours. More time would likely help there.
- **On pizza a quarter of the runs found their pick before 69% of their nodes** (C4 seed 4 at node 15 of 111). Extra time there mostly produced nodes that did not beat the pick on validation.
- **Insults sits between the two.**

## 3. How optimism grows during a run

On pizza the current best-validation node grows more optimistic as the run goes on, and falls further behind the best node on test; on spooky neither changes.

| Share of the run | Spooky: test − validation | Insults | Pizza | Spooky: loss to best node | Insults | Pizza |
| --- | --- | --- | --- | --- | --- | --- |
| 25% | −0.007 | +0.010 | −0.016 | 0.000 | 0.002 | 0.005 |
| 50% | −0.006 | +0.003 | −0.017 | 0.001 | 0.002 | 0.009 |
| 75% | −0.007 | 0.000 | −0.021 | 0.001 | 0.004 | 0.012 |
| 100% | −0.006 | −0.001 | −0.021 | 0.000 | 0.003 | 0.009 |

Medians over the runs with A1; test − validation is oriented so that negative means validation looks better than test. The more nodes compete on a small validation split, the more the winner's validation score is luck: pizza shows this, spooky (3,524 validation rows) does not.

## 4. One test of the conditions across tasks

No condition differs from another across the three tasks.

- **C1, C4 and C5** (15 blocks: 3 tasks × 5 seeds, scores ranked within each block): Friedman χ² = 1.2, p = 0.55. Mean ranks (1 = best of 3): C5 1.8, C1 2.0, C4 2.2.
- **All five conditions** (9 blocks: 3 tasks × seeds 0–2): Friedman χ² = 2.2, p = 0.69. Mean ranks (1 = best of 5): C1 2.6, C5 2.8, A4-off 2.9, A1-off 3.2, C4 3.6.

Source: `runs/_analysis/full_plan/extra_analyses.py` and its CSVs (`extra_sel.csv`, `extra_time.csv`, `extra_gap.csv`).
