# NOMAD2018 - Full Four-Hour Experiment Results

## Experiment Setup

- Task: nomad2018-predict-transparent-conductors
- Model: deepseek/deepseek-v4-flash-0731
- Provider: OpenRouter
- Sandbox: Docker (2 CPUs, 4 GB RAM)
- Nominal budget: 4 hours per run
- Total automated runs: 21
- C1, C4, C5: 5 seeds each (0-4)
- A1-off, A4-off: 3 seeds each (0-2)
- C2 and C3: Post-hoc analyses of C1, not independent runs

## Official MLE-bench Outcomes

| Condition | Runs | Valid submissions | Mean test RMSLE |
|---|---:|---:|---:|
| C1 | 5 | 5 | 0.06089 |
| C4 | 5 | 5 | 0.06165 |
| C5 | 5 | 3 | 0.06146 |
| A1-off | 3 | 2 | 0.06102 |
| A4-off | 3 | 2 | 0.05907 |

Mean test RMSLE is calculated only from valid submissions. Invalid runs are included in submission-success rates.

Overall, 17 of 21 runs produced valid submissions. All 17 valid submissions earned medals.

## Automated Interventions

- C4: Two pruning interventions, both in seed 0.
- C5: Two finding corrections, both in seed 0.
- All four interventions were successfully applied.
- No interventions were dropped.
- No additional C4 or C5 interventions occurred in the newly added seeds.

## Validation-Test Gap

| Condition | Mean final gap |
|---|---:|
| C1 | -0.000296 |
| C4 | 0.001286 |
| C5 | 0.000198 |
| A1-off | 0.004679 |
| A4-off | 0.001460 |

Positive gaps indicate optimistic validation performance.

A1-off had the largest observed positive gap, but only two runs produced valid final scores.

## API Cost

Total recorded API cost across the 21 runs: approximately USD 4.24.

| Condition | Mean cost per run (USD) |
|---|---:|
| C1 | 0.2384 |
| C4 | 0.2833 |
| C5 | 0.1766 |
| A1-off | 0.1192 |
| A4-off | 0.1292 |

Recorded costs are based on API usage logs and may differ from final provider billing.

## Failed Runs and Infrastructure Diagnostics

Four runs completed their nominal budgets without producing submissions:

- C5 seed 3: 11 buggy nodes, no working nodes.
- C5 seed 4: 7 buggy nodes, no working nodes.
- A1-off seed 2: 11 buggy nodes, no working nodes.
- A4-off seed 2: 10 buggy nodes, no working nodes.

Across these runs, 38 nodes were terminated by execution timeouts, and one node was rejected by the leakage detector.

Docker Desktop and WSL2 experienced execution instability during the experiment period.

A diagnostic replay of the original C5 seed 3 node n0 script, after restarting Windows, terminated with a Python TypeError in approximately 3.09 seconds rather than timing out.

After correcting the NumPy clip argument in a separate diagnostic copy, the script generated predictions successfully in approximately 4.84 seconds.

These observations suggest that execution-environment instability may have contributed to the historical timeouts. However, the cause of every timeout has not been established.

The four original failed runs are retained as invalid submissions. No original checkpoints or generated scripts were modified for this diagnostic.

## Limitations

- Only 3-5 seeds per condition.
- Four missing submissions, possibly affected by infrastructure instability.
- Mean test scores exclude invalid runs.
- Some runs exceeded the nominal four-hour budget.
- Interventions were rare, limiting conclusions about their effectiveness.
- The experiment used one language model and one machine.

## Directory Structure

- grades/: Official MLE-bench grading results for all 21 runs.
- analysis/outcomes/: Submission validity, medal rates and test scores.
- analysis/interaction/: Intervention frequency and timing.
- analysis/val_test_gap/: Validation-test gap statistics.
- analysis/cost/: Token usage, API costs and execution statistics.
- interventions/: Applied C4 and C5 intervention records.

The original two-hour results and the C6 human-supervised session are one folder up, in [`../`](../nomad.md) (`docs/results/nomad/`).
