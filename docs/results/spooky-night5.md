# Spooky: A4-off seed 2 and C1 seed 3

Night of 1 to 2 Nov 2026, Nabil's Mac. Two new 4-hour runs from the full plan: A4-off seed 2, which gives both ablations three seeds, and C1 seed 3, the first run of seeds 3 and 4.

Spooky is multiclass log loss, so **lower is better**. MLE-bench thresholds: median 0.4188, bronze 0.2938.

## Setup

- **The same as the 4-hour nights before:** DeepSeek V4 Flash 0731 (fp8), A1, Docker with Colima at 2 CPUs and 4 GB, on the MacBook Pro M1.
- **Started with `cloud_run.py` directly,** since `configs/schedule.yaml` still lists only the half plan's seeds:
  ```
  python scripts/cloud_run.py --config configs/conditions/ablation_a4_off.yaml --task spooky-author-identification \
      --seed 2 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  python scripts/cloud_run.py --config configs/conditions/c1_autonomous.yaml --task spooky-author-identification \
      --seed 3 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  ```
- **Times (SGT):** A4-off 23:24 to 03:24, C1 03:24 to 07:24. Both ran 4 hours in one go.
- **Health:** no restarts.
- **Cost:** about $0.27.
- **Cut-off calls:** 1 on A4-off and 3 on C1, all served by StreamLake, losing 11 and 32 minutes. From the next spooky night on, StreamLake is excluded (`configs/base.yaml`, the same change as on main). These two runs still used it.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) |
|---|---|---|---|---|---|
| A4-off seed 2 | 43 | **0.3472** | n41: 0.3428 / 0.3390 | 0.3471 | 0.3471 |
| C1 seed 3 | 32 | **0.3672** | n30: 0.3650 / 0.3810 | 0.3672 | 0.3672 |

- **Both are above the median, and neither medalled.**
- **The pick is the best node, or within 0.0001 of it,** in both runs.
- **The C4 rule, replayed (`scripts/replay_policy.py`), doesn't fire** on either run.

## Findings

### 1. C1 seed 3 is the weakest C1, and never used naive Bayes

At 0.3672, C1 seed 3 is 0.07 worse than C1 seed 2.
- **Its pick doesn't combine naive Bayes with a linear model.** Only 2 of its 32 nodes tried naive Bayes at all. In the half plan's 14 spooky runs, every score below 0.34 came from that combination ([`spooky-drops.md`](spooky-drops.md)).
- **It made only 32 nodes,** the fewest of any 4-hour spooky run, partly because 32 minutes went to cut-off calls.

### 2. A4-off seed 2 used naive Bayes, and landed in the middle

A4-off's pick is a stacking ensemble that includes naive Bayes, and its final node added a logistic regression on SVD components of word TF-IDF. At 0.3472, it's between A4-off's seeds 0 and 1. Test stayed within 0.017 of validation on every node.

### 3. Where spooky stands at 4 hours

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Mean |
|---|---|---|---|---|---|
| C1 | 0.3198 | 0.3029 | 0.2944 | **0.3672** | 0.3211 |
| C4 | 0.3808 | 0.3131 | 0.3336 | to run | 0.3425 |
| C5 | 0.3360 | 0.2816 (bronze) | 0.3352 | to run | 0.3176 |
| A1-off | 0.3440 | 0.4078 | 0.3257 | – | 0.3592 |
| A4-off | 0.3215 | 0.3584 | **0.3472** | – | 0.3424 |

- **C5 now has the best mean,** since C1 seed 3 pulled C1's mean from 0.3057 to 0.3211.
- **C1's own spread is now 0.073,** larger than any gap between two conditions' means. One more seed per condition won't settle the order.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| A4-off seed 2 | [A4-off-seed2.png](spooky-night5/trajectories/A4-off-seed2.png) | [A4-off-seed2.md](spooky-night5/trajectories/A4-off-seed2.md) |
| C1 seed 3 | [C1-seed3.png](spooky-night5/trajectories/C1-seed3.png) | [C1-seed3.md](spooky-night5/trajectories/C1-seed3.md) |

## Files

- **`spooky-night5/grades/`:** MLE-bench's grade of each run.
- **`spooky-night5/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders (`runs/grid/A4-off_spooky-author-identification_seed2/`, `runs/grid/C1_spooky-author-identification_seed3/`) and the log (`runs/grid_spooky_night5.log`).

## Next

The rest of the full plan for spooky is 5 runs at 4 hours, about 20 hours: C4 and C5 seed 3, and C1, C4 and C5 seed 4. These will run without StreamLake.
