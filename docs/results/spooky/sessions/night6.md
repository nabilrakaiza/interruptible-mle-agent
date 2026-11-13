# Spooky: C4 and C5 seed 3

Night of 2 to 3 Nov 2026, Nabil's Mac. Two new 4-hour runs from the full plan: C4 seed 3 and C5 seed 3, which give C1, C4 and C5 four seeds each. The first spooky night without StreamLake.

Spooky is multiclass log loss, so **lower is better**. MLE-bench thresholds: median 0.4188, bronze 0.2938.

## Setup

- **The same as the 4-hour nights before:** DeepSeek V4 Flash 0731 (fp8), A1, Docker with Colima at 2 CPUs and 4 GB, on the MacBook Pro M1.
- **StreamLake excluded** from the LLM routing (`73caabb`), as on Kaggle from round 2.
- **Started with `cloud_run.py` directly** (`runs/night6_spooky.sh`, one after the other):
  ```
  python scripts/cloud_run.py --config configs/conditions/c4_divergence_prune.yaml --task spooky-author-identification \
      --seed 3 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  python scripts/cloud_run.py --config configs/conditions/c5_finding_correction.yaml --task spooky-author-identification \
      --seed 3 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  ```
- **Times (SGT):** C4 23:33 to 03:34, C5 03:34 to 07:34. Both ran 4 hours in one go.
- **Health:** no restarts.
- **Cost:** about $0.46.
- **Cut-off calls:** 1 on C4 (4 minutes) and none on C5, against 1 and 3 (11 and 32 minutes) on the night before with StreamLake.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Interventions |
|---|---|---|---|---|---|---|
| C4 seed 3 | 55 | **0.3214** | n53: 0.3161 / 0.3192 | 0.3214 | 0.3214 | none fired |
| C5 seed 3 | 131 | **0.3001** | n128: 0.2969 / 0.2973 | 0.3001 | 0.3001 | none fired |

- **Both are above the median, and neither medalled.** C5 is 0.006 short of bronze.
- **Both picked their best node on test.** Test stayed within 0.016 of validation on every node.
- **No interventions:** neither C4 nor C5 fired, and the C4 rule, replayed on C5 (`scripts/replay_policy.py`), doesn't fire either.

## Findings

### 1. Both picks combine naive Bayes with a linear model

- **C4's pick** stacks BernoulliNB and ComplementNB with logistic regressions on word and character n-grams.
- **C5's pick** combines ComplementNB with a calibrated SGD classifier. 122 of its 131 nodes used naive Bayes.

Both land below 0.34, as every run with that combination has ([`../drops.md`](../drops.md)). C1 seed 3, the night before, never used it and scored 0.367.

### 2. C4 made 55 nodes, C5 131, in the same 4 hours

The difference is the scripts, not the LLM: C4's took a median 3.3 minutes per node against C5's 1.4, with heavier character n-gram features and more models per stack. C4 found its best node at n53 of 55, so it was still improving when the budget ran out.

### 3. Where spooky stands at 4 hours

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Mean |
|---|---|---|---|---|---|
| C1 | 0.3198 | 0.3029 | 0.2944 | 0.3672 | 0.3211 |
| C4 | 0.3808 | 0.3131 | 0.3336 | **0.3214** | 0.3372 |
| C5 | 0.3360 | 0.2816 (bronze) | 0.3352 | **0.3001** | **0.3132** |
| A1-off | 0.3440 | 0.4078 | 0.3257 | – | 0.3592 |
| A4-off | 0.3215 | 0.3584 | 0.3472 | – | 0.3424 |

- **C5 keeps the best mean,** 0.008 ahead of C1. C4 is 0.024 behind C5.
- **Each condition's own spread is wider than those gaps:** 0.073 for C1, 0.068 for C4 and 0.054 for C5. Four seeds don't settle the order.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C4 seed 3 | [C4-seed3.png](night6/trajectories/C4-seed3.png) | [C4-seed3.md](night6/trajectories/C4-seed3.md) |
| C5 seed 3 | [C5-seed3.png](night6/trajectories/C5-seed3.png) | [C5-seed3.md](night6/trajectories/C5-seed3.md) |

## Files

- **`night6/grades/`:** MLE-bench's grade of each run.
- **`night6/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders (`runs/grid/C4_spooky-author-identification_seed3/`, `runs/grid/C5_spooky-author-identification_seed3/`), the launcher (`runs/night6_spooky.sh`) and the log (`runs/grid_spooky_night6.log`).

## Next

The rest of the full plan for spooky is 3 runs at 4 hours, 12 hours: C1, C4 and C5 seed 4.
