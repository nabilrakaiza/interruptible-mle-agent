# Leaf: results of the half plan

Medhini's 13 runs on `leaf-classification`: seeds 0, 1 and 2 of C1, C4 and C5, and seeds 0 and 1 of A1-off and A4-off, plus one C6 session. Medhini's own package, with the grades, outcomes, C6 notes and her findings, is in [`leaf/`](leaf/findings.md). This page summarises it in the format of the other tasks, and every number here comes from that package.

Leaf classifies 99 tree species from leaf images and 192 precomputed shape, margin and texture features. The metric is multiclass log loss, so **lower is better**. MLE-bench thresholds: median 0.1083, bronze 0.0153, silver 0.0079, gold 0.0.

## Setup

- **The same as the other tasks:** DeepSeek V4 Flash 0731, A1, Docker, 2 hours per run.
- **The machine isn't recorded** in the package.
- **Splits:** the A1 harness for leaf holds out 178 validation rows, 89 probe rows and 99 test rows. That is one or two rows per species in each.

## Test scores

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.06014 | 0.02633 | 0.01277 (bronze) | 0.03308 |
| C2 (oracle, from C1) | 0.04689 | 0.01593 | 0.00558 | 0.02280 |
| C3 (top 3, from C1) | 0.05951 | 0.01593 | 0.01277 | 0.02940 |
| C4 | **0.00145 (silver)** | 0.19893 | 0.03698 | 0.07912 |
| C5 | 0.36408 | 0.06125 | 0.08460 | 0.16998 |
| A1-off | 0.00932 (bronze) | **15.65532** | n/a | 7.83232 |
| A4-off | 0.36408 | 0.18617 | n/a | 0.27512 |
| C6 (seed 100) | 0.02606 | | | |

- **Three runs medalled:** C4 seed 0 (silver), C1 seed 2 (bronze) and A1-off seed 0 (bronze).
- **Four runs were below the median:**
  - C4 seed 1 (0.199);
  - C5 seed 0 (0.364);
  - A4-off seed 0 (0.364);
  - A1-off seed 1 (15.66).
- **Single runs drive the means.** C5's and A4-off's means each rest on one run at 0.364, and A1-off's on one run at 15.66. A log loss that large usually means confident wrong predictions on many rows, but the package doesn't say what that run did. Without those runs, the conditions are much closer.

## Final selection matters on leaf

How much the oracle pick (C2) gains over C1's own pick:

| Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|
| 0.0133 | 0.0104 | 0.0072 | **0.0103** (about a third of C1's mean) |

- **On the other tasks the oracle gained under 2%.** On leaf it would cut C1's loss by about a third.
- **The C6 run shows the same:**
  - the pick, n33, ranked 7th of 44 on test (0.0261);
  - the best node, n42, scored 0.0119, which would be a bronze medal;
  - n42 ranked 13th on validation.
- **Validation is unreliable on leaf.** In the C6 run, the pick's validation loss was 0.0009, while its probe was 0.179 and its test 0.026. Most top nodes sit near zero on validation, so validation can't tell them apart: with 178 rows for 99 species, a model can get every validation row right and still miss a test leaf.

## C6 live session

Medhini ran one C6 session, seed 100, 2 hours. Notes and debrief are in [`leaf/c6/c6_notes.md`](leaf/c6/c6_notes.md), with the chart and timeline in [`leaf/c6/`](leaf/c6/timeline.md).

- **No interventions.** The participant watched the dashboard but wasn't sure which changes justified a prune or a redirect.
- **The result:** 49 nodes, test 0.0261. That is above the median, with no medal.
- **What would have helped:** clearer guidance on when to act, especially when validation improves while the probe gets worse.
- **The chart shows what a monitor was looking at:**
  - validation sat near zero from about n15 onwards;
  - the probe moved between 0.1 and 0.36;
  - so the gap between validation and probe was large all the time, and not a useful signal.

## Points to check with Medhini

- **Whether C4 or C5 acted** in a live run. The package has no intervention logs.
- **What happened in A1-off seed 1** (15.66). It's the worst run of the half plan by far.
- **The machine and Docker setup.**
- **Trajectories for the grid runs.** Only the C6 session has one.
