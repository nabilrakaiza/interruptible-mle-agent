# NOMAD2018 — Interruptible MLE Agent Results

## Experiment Overview

This directory contains the results of running the interruptible MLE agent on the Kaggle competition `nomad2018-predict-transparent-conductors`.

All 13 scheduled experiments were completed using DeepSeek V4 Flash 0731 through OpenRouter, with Docker execution and a nominal two-hour budget per run.

The experiments cover five conditions: C1 (autonomous baseline), C4 (divergence pruning), C5 (finding correction), A1-off (evaluation ablation), and A4-off (reflection ablation).

## Official MLE-bench Results

Lower scores indicate better performance.

| Condition | Runs | Mean Score | Valid Submissions | Medal Rate |
|---|---:|---:|---:|---:|
| C1 — Autonomous | 3 | 0.06229 | 100% | 100% |
| C4 — Divergence Pruning | 3 | 0.06102 | 100% | 100% |
| C5 — Finding Correction | 3 | 0.06146 | 100% | 100% |
| A1-off — Evaluation Ablation | 2 | 0.06102 | 100% | 100% |
| A4-off — Reflection Ablation | 2 | 0.05907 | 100% | 100% |

All 13 submissions scored above the competition median and earned either silver or bronze medals.

C2 (oracle final selection) and C3 (top-k hedge) were also evaluated post hoc from the C1 search trees, with mean scores of 0.06159 and 0.06188 respectively. These were not separate agent runs.

## Intervention Analysis

**C4 — Divergence Pruning**

Two pruning interventions were applied in seed 0, targeting nodes `n19` and `n44`. These actions marked 30 nodes as pruned across two subtrees.

No pruning interventions were recorded in seeds 1 or 2, although the monitor was enabled in both runs.

**C5 — Finding Correction**

Two correction interventions were applied in seed 0, targeting findings `f-991501ad13` and `f-70af62be3b`.

The corrections were triggered by failed replication evidence involving buggy nodes `n12` and `n14`. Both targeted findings were absent from the following checkpoints.

No correction interventions were recorded in seeds 1 or 2.

## Validation–Test Generalization

Mean final validation–test gaps:

| Condition | Mean Gap |
|---|---:|
| C1 | -0.000112 |
| C4 | 0.000193 |
| C5 | 0.000198 |
| A1-off | 0.004679 |
| A4-off | 0.001460 |

A1-off exhibited the largest observed gap, suggesting that removing the evaluation harness may affect the reliability of validation feedback. The small sample size limits interpretation.

## API Cost and Efficiency

| Condition | Mean Nodes | Mean API Cost (USD) |
|---|---:|---:|
| C1 | 28.3 | $0.139 |
| C4 | 72.3 | $0.119 |
| C5 | 57.0 | $0.203 |
| A1-off | 50.5 | $0.147 |
| A4-off | 88.5 | $0.144 |

API costs are taken from the experiment's logged provider-reported values.

## Limitations

- Only two or three seeds were run per condition.
- Intervention actions occurred in only one of three C4 runs and one of three C5 runs.
- Some experiments exceeded the nominal two-hour wall-clock budget.
- Differences in final scores cannot be attributed causally to individual interventions.
- Post-hoc oracle selection uses private test information and is not a deployable model-selection strategy.

## Directory Structure

- `grades/` — Official MLE-bench grading results for all 13 runs.
- `interventions/` — Applied C4 and C5 intervention records.
- `analysis/outcomes/` — Outcome summaries and per-run scores.
- `analysis/interaction/` — Intervention frequency and timing.
- `analysis/val_test_gap/` — Validation–test generalization analysis.
- `analysis/cost/` — Token usage, API costs, and execution statistics.

The full experiment checkpoints and generated scripts are retained separately and are not included in this compact results package.