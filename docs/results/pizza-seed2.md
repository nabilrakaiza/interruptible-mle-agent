# Pizza, seed 2: Kaggle round 3

3 Nov 2026, on Kaggle. Seed 2 of all five conditions on `random-acts-of-pizza`, round 3 of this task's full plan (`configs/kaggle_sessions.yaml`). Seeds 0 and 1 are in [`pizza-seed0.md`](pizza-seed0.md) and [`pizza-seed1.md`](pizza-seed1.md). Insults' half of the same sessions is on the `result-insults` branch.

Pizza is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.5996, bronze 0.6921, silver 0.7648, gold 0.9791. Validation has 576 rows and the probe 288.

## Setup

- **The same as seed 1** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours, StreamLake excluded).
- **Code:** `30b2f95` on main. The only change since seed 1 is in `kaggle_collect.py` (downloads), not in the agent.
- **Times (SGT):** 02:08 to 06:10, sessions 11 to 15, after each session's insults run.
- **Cost:** about $1.23 for the five runs ($2.86 on seed 1).
- **Health:** no restarts. Every run stopped on its 4-hour budget.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Interventions | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|---|
| C1 | 147 | **0.7095 (bronze)** | n128: 0.7235 / 0.6592 | 0.7095 | 0.7095 | – | 0 |
| C4 | 116 | **0.6771** | n109: 0.7176 / 0.6794 | 0.7118 | 0.6936 | none fired | 5 |
| C5 | 119 | **0.6829** | n109: 0.7316 / 0.6960 | 0.6997 | 0.6832 | 1 correction | 5 |
| A1-off | 84 | **0.6899** | n61: 0.7345 / 0.6937 | 0.6985 | 0.6899 | – | 0 |
| A4-off | 67 | **0.6822** | n63: 0.7109 / 0.6833 | 0.6893 | 0.6849 | – | 0 |

- **Only C1 got bronze,** with its best node: its pick is also the best on test.
- **The pick is up to 0.035 below the best node on test** (C4), and 0.017 on C5.

## Findings

### 1. Three seeds: C1 leads by 0.009, with two bronzes of three

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.6842 | 0.6932 (bronze) | **0.7095 (bronze)** | **0.6956** |
| C4 | 0.6692 | 0.7060 (bronze) | 0.6771 | 0.6841 |
| C5 | 0.7008 (bronze) | 0.6753 | 0.6829 | 0.6863 |
| A1-off | 0.6700 | 0.6954 (bronze) | 0.6899 | 0.6851 |
| A4-off | 0.6553 | 0.7078 (bronze) | 0.6822 | 0.6818 |

- **C1 now has the best mean,** 0.009 above C5, and is the only condition with two bronzes.
- **That gap is smaller than one condition's spread:** A4-off ranges over 0.053 across its seeds, C4 over 0.037. Three seeds can't separate C1 from the rest.

### 2. C4's pick lost 0.035 to a near-tie on validation

C4's top five nodes on validation are within 0.003 of each other (0.715 to 0.718), but their test scores range from 0.677 to 0.694. The pick, n109 (tied on validation with n113), is the lowest of them. The best node on test, n47 (0.712), sits at 0.696 on validation.
- **The top-3 hedge (C3) recovers 0.017 here,** the most it has on any pizza run.
- **The probe didn't point the right way either:** its best node, n63, scores 0.690 on test.

As on seed 1, with 576 validation rows, the best validation score is partly luck.

### 3. C5's one correction removed a finding that was right

At safe point 15 (after n14), C5 deleted the finding "rolling request-volume counts (1, 7 and 30 days) improved validation from 0.692 (n11) to 0.698 (n13)". The rule flagged it because one cited node, n11, failed to replicate against its own parent n4: validation +0.008 but probe −0.027.
- **The finding itself held up:** n13 beat n11 on validation, probe and test (0.673 against 0.670).
- **It changed nothing:** the agent kept the features, and its pick n109 still computes them.

This is the same weakness as on seed 1: with a 288-row probe, "failed to replicate" is often noise, and here it was about the baseline, not the change the finding claims.

### 4. The C4 rule, replayed, fires once and changes nothing

C4 itself never fired. Replayed on the other runs (`scripts/replay_policy.py`), the rule fires on A4-off only: after n41 it prunes 51 nodes, and the pick becomes n3, at test 0.6823 against 0.6822.

### 5. Almost no cut-off calls this time

2 of 587 calls were cut off at the 64k-token cap (0.3%), against 6.0% on seed 1 and 12.2% on seed 0. On pizza this round, the routing gave each run its full 4 hours.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 | [C1.png](pizza-seed2/trajectories/C1.png) | [C1.md](pizza-seed2/trajectories/C1.md) |
| C4 | [C4.png](pizza-seed2/trajectories/C4.png) | [C4.md](pizza-seed2/trajectories/C4.md) |
| C5 | [C5.png](pizza-seed2/trajectories/C5.png) | [C5.md](pizza-seed2/trajectories/C5.md) |
| A1-off | [A1-off.png](pizza-seed2/trajectories/A1-off.png) | [A1-off.md](pizza-seed2/trajectories/A1-off.md) |
| A4-off | [A4-off.png](pizza-seed2/trajectories/A4-off.png) | [A4-off.md](pizza-seed2/trajectories/A4-off.md) |

## Files

- **`pizza-seed2/grades/`:** MLE-bench's grade of each run.
- **`pizza-seed2/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders, in `runs/kaggle/*_random-acts-of-pizza_seed2/`.

## Next

The ablations are done (seeds 0 to 2). Round 4 (sessions 16 to 20) runs C1, C4 and C5 seed 3 and C1 and C4 seed 4; round 5 (session 21) is C5 seed 4.
