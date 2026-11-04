# Spooky: C1 seed 4

Night of 3 to 4 Nov 2026, Nabil's Mac. One new 4-hour run from the full plan: C1 seed 4, which gives C1 all five seeds.

Spooky is multiclass log loss, so **lower is better**. MLE-bench thresholds: median 0.4188, bronze 0.2938.

## Setup

- **The same as the night before** ([`spooky-night6.md`](spooky-night6.md)): DeepSeek V4 Flash 0731 (fp8), A1, Docker with Colima at 2 CPUs and 4 GB, on the MacBook Pro M1, StreamLake excluded.
- **Started with `cloud_run.py` directly** (`runs/night7_spooky.sh`):
  ```
  python scripts/cloud_run.py --config configs/conditions/c1_autonomous.yaml --task spooky-author-identification \
      --seed 4 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  ```
- **Times (SGT):** 23:46 to 03:46, in one go.
- **Health:** no restarts.
- **Cost:** about $0.15.
- **Cut-off calls:** none.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) |
|---|---|---|---|---|---|
| C1 seed 4 | 48 | **0.3608** | n45: 0.3587 / 0.3782 | 0.3608 | 0.3608 |

- **Above the median, no medal.** The pick is the run's best node on test, and test is within 0.002 of validation.
- **The C4 rule, replayed (`scripts/replay_policy.py`), doesn't fire.**

## Findings

### 1. C1 seed 4 barely used naive Bayes, and stayed above 0.36

The pick is a single logistic regression on word and character TF-IDF features, with no naive Bayes. Only 5 of the 48 nodes used naive Bayes at all, and no node scored below 0.36. That matches C1 seed 3 (0.367, 2 of 32 nodes with naive Bayes) and the pattern in [`spooky-drops.md`](spooky-drops.md): every spooky run below 0.34 submitted naive Bayes combined with a linear model.

So C1's two weakest seeds are the two that didn't find that combination. On spooky, which model family the agent lands on seems to matter more than the condition.

### 2. Where spooky stands at 4 hours

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean |
|---|---|---|---|---|---|---|
| C1 | 0.3198 | 0.3029 | 0.2944 | 0.3672 | **0.3608** | 0.3290 |
| C4 | 0.3808 | 0.3131 | 0.3336 | 0.3214 | to run | 0.3372 |
| C5 | 0.3360 | 0.2816 (bronze) | 0.3352 | 0.3001 | to run | **0.3132** |
| A1-off | 0.3440 | 0.4078 | 0.3257 | – | – | 0.3592 |
| A4-off | 0.3215 | 0.3584 | 0.3472 | – | – | 0.3424 |

- **C5 keeps the best mean,** now 0.016 ahead of C1, whose mean rose from 0.3211 to 0.3290.
- **C1's spread is 0.073,** still wider than any gap between two conditions' means.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 seed 4 | [C1-seed4.png](spooky-night7/trajectories/C1-seed4.png) | [C1-seed4.md](spooky-night7/trajectories/C1-seed4.md) |

## Files

- **`spooky-night7/grades/`:** MLE-bench's grade of the run.
- **`spooky-night7/trajectories/`:** its chart and timeline.
- **On Nabil's Mac only:** the run folder (`runs/grid/C1_spooky-author-identification_seed4/`), the launcher (`runs/night7_spooky.sh`) and the log (`runs/grid_spooky_night7.log`).

## Next

The rest of the full plan for spooky is 2 runs at 4 hours, 8 hours: C4 and C5 seed 4.
