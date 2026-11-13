# Spooky: C4 and C5 seed 4, and the full plan

Night of 4 to 5 Nov 2026, Nabil's Mac. The last two 4-hour runs of the full plan: C4 seed 4 and C5 seed 4. With them, spooky has all 21 runs at 4 hours.

Spooky is multiclass log loss, so **lower is better**. MLE-bench thresholds: median 0.4188, bronze 0.2938.

## Setup

- **The same as the nights before** ([`night6.md`](night6.md), [`night7.md`](night7.md)): DeepSeek V4 Flash 0731 (fp8), A1, Docker with Colima at 2 CPUs and 4 GB, on the MacBook Pro M1, StreamLake excluded.
- **Started with `cloud_run.py` directly** (`runs/night8_spooky.sh`, one after the other):
  ```
  python scripts/cloud_run.py --config configs/conditions/c4_divergence_prune.yaml --task spooky-author-identification \
      --seed 4 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  python scripts/cloud_run.py --config configs/conditions/c5_finding_correction.yaml --task spooky-author-identification \
      --seed 4 --budget-hours 4.0 --sandbox docker --runs-root runs/grid --evaluator a1
  ```
- **Times (SGT):** C4 23:09 to 03:09, C5 03:09 to 07:09. Both ran 4 hours in one go.
- **Health:** no restarts.
- **Cost:** about $0.44.
- **Cut-off calls:** none.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Interventions |
|---|---|---|---|---|---|---|
| C4 seed 4 | 159 | **0.3236** | n150: 0.3082 / 0.3088 | 0.3236 | 0.3236 | none fired |
| C5 seed 4 | 49 | **0.3136** | n46: 0.3006 / 0.3028 | 0.3136 | 0.3136 | none fired |

- **Both are above the median, and neither medalled.**
- **Both picked their best node on test.** C4's pick is 0.015 worse on test than on validation, the largest gap of any spooky run with A1.
- **The C4 rule, replayed on C5 (`scripts/replay_policy.py`), doesn't fire.**
- **C4 made 159 nodes,** the most of any spooky run, and 151 of them used naive Bayes. Its pick is ComplementNB alone, with no linear model. C5's pick combines three naive Bayes variants with logistic regression.

## The full plan: 21 runs

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean | SD |
|---|---|---|---|---|---|---|---|
| C1 | 0.3198 | 0.3029 | 0.2944 | 0.3672 | 0.3608 | 0.3290 | 0.033 |
| C4 | 0.3808 | 0.3131 | 0.3336 | 0.3214 | **0.3236** | 0.3345 | 0.027 |
| C5 | 0.3360 | 0.2816 (bronze) | 0.3352 | 0.3001 | **0.3136** | **0.3133** | 0.023 |
| A1-off | 0.3440 | 0.4078 | 0.3257 | – | – | 0.3592 | 0.043 |
| A4-off | 0.3215 | 0.3584 | 0.3472 | – | – | 0.3424 | 0.019 |

Every run is at 4 hours: seeds 0 to 2 of the half plan were extended from 2 hours ([`seed0-4h.md`](seed0-4h.md) and after), and the rest ran 4 hours from the start.

### 1. C5 has the best mean, but the conditions aren't separated

- **C5's mean is 0.016 better than C1's and 0.021 better than C4's,** and it has the only medal (seed 1).
- **Each condition's own seeds range over 0.037 to 0.082,** more than any gap between means. Five seeds don't settle the order.
- **C5's lead doesn't come from its interventions** (finding 3): in three of its five runs it never fired.

### 2. A1 is what matters most

- **A1-off has the worst mean (0.3592) and the widest spread.** Its seed 1 leaked: validation 0.152 against test 0.408, a gap of 0.256. Its seed 0's gap is 0.088.
- **With A1 on (18 runs), test stays within 0.015 of validation on every run,** and the pick is never more than 0.009 behind the run's best node on test.

### 3. The interventions had almost nothing to do

- **C4 never fired in its 5 live runs.** With A1 on, validation and the probe moved together.
- **C5 fired twice in 5 runs** (seeds 0 and 2), once over a finding that cited a crashed node and once a likely false positive ([`../spooky.md`](../spooky.md)). Neither changed the pick.
- **The C4 rule, replayed on the C1, C5 and ablation runs, fires on 3:**
  - **A1-off seed 1:** it catches the leak, and the pick improves from 0.408 to 0.314;
  - **A1-off seed 0:** the pick gets slightly worse (0.344 to 0.346);
  - **C5 seed 1:** the pick gets slightly worse (0.282 to 0.285), still bronze.

So the rule helps where the agent's own validation is broken, which A1 already prevents.

### 4. Naive Bayes with a linear model: still the top, no longer a rule

The 9 best runs all submitted naive Bayes combined with a linear model (by the classes their scripts import). Below that the pattern blurs: 4 of the 14 runs under 0.34 didn't, including C4 seed 4 (0.324, ComplementNB alone). The half plan's rule in [`../drops.md`](../drops.md) ("every run below 0.34 combined them") came from 2-hour runs and doesn't survive the extra time and seeds. The weakest A1 runs (C4 seed 0, C1 seeds 3 and 4) are still all without the combination.

### 5. Cost and cut-off calls

- **About $3.65 for all 21 runs,** including the half plan's 2-hour runs and their extensions.
- **17 of 1,626 calls were cut off,** all but one before StreamLake was excluded (2 Nov).

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C4 seed 4 | [C4-seed4.png](night8/trajectories/C4-seed4.png) | [C4-seed4.md](night8/trajectories/C4-seed4.md) |
| C5 seed 4 | [C5-seed4.png](night8/trajectories/C5-seed4.png) | [C5-seed4.md](night8/trajectories/C5-seed4.md) |

## Files

- **`night8/grades/`:** MLE-bench's grade of each run.
- **`night8/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders (`runs/grid/C4_spooky-author-identification_seed4/`, `runs/grid/C5_spooky-author-identification_seed4/`), the launcher (`runs/night8_spooky.sh`) and the log (`runs/grid_spooky_night8.log`).

## Next

Spooky's full plan is done. Its C6 session (seed 100) ran 2 hours; compared with C1 at the 2-hour mark (mean 0.344 over five seeds), its 0.368 is within C1's range.
