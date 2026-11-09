# Insults, round 5: C5 seed 4, and the full plan

3 to 4 Nov 2026, on Kaggle. Session 21, the last of this task's full plan (`configs/kaggle_sessions.yaml`): C5 seed 4. With it, insults has all 21 runs. The earlier rounds are in [`seed0.md`](seed0.md), [`seed1.md`](seed1.md), [`seed2.md`](seed2.md) and [`round4.md`](round4.md). Pizza's half of the session is on the `result-pizza` branch.

Insults is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.7784, bronze 0.7911, silver 0.8231, gold 0.8332.

## Setup

- **The same as rounds 3 and 4** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours, StreamLake excluded).
- **Code:** `30b2f95` on main.
- **Times (SGT):** 23:37 to 03:37, in `imle-slot-1`.
- **Cost:** about $0.46.
- **Health:** no restarts. The run stopped on its 4-hour budget.

## Result

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|
| C5 seed 4 | 112 | **0.9074 (gold)** | n106: 0.9127 / 0.9224 | 0.9095 | 0.9074 | 10 |

- **Gold, 0.002 below the run's best node.**
- **C5 didn't fire,** and the C4 rule, replayed (`scripts/replay_policy.py`), doesn't fire either.

## The full plan: 21 runs

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean | SD |
|---|---|---|---|---|---|---|---|
| C1 | 0.9021 | 0.9058 | 0.9059 | 0.8928 | 0.9030 | 0.9019 | 0.0054 |
| C4 | 0.9041 | 0.9043 | 0.9098 | 0.9083 | 0.9007 | 0.9054 | 0.0037 |
| C5 | 0.9004 | 0.9115 | 0.9157 | 0.9020 | **0.9074** | 0.9074 | 0.0064 |
| A1-off | 0.9037 | 0.9021 | 0.9127 | – | – | 0.9062 | 0.0057 |
| A4-off | 0.9083 | 0.9126 | 0.9111 | – | – | **0.9107** | 0.0022 |

### 1. Every run is gold, and the conditions can't be told apart

- **21 golds out of 21.** The lowest run (C1 seed 3, 0.8928) is still 0.06 above the gold line, so medal rates say nothing about the conditions.
- **The means are within 0.009** (C1's 0.9019 to A4-off's 0.9107). A single condition's seeds range up to 0.015 (C5). No ranking is claimed.

### 2. No intervention ever had work to do on insults

- **Neither C4 nor C5 fired in any of their 10 runs.**
- **The C4 rule, replayed on every C1, C5 and ablation run, never fired either.**

On insults the validation and probe move together: the median node's probe sits a steady 0.005 to 0.03 above its validation in every run, and the C4 rule only looks at changes, so it never sees the two diverge. With nothing to correct, C4 and C5 runs are C1's agent on other random paths.

### 3. Picking by validation costs little

- **The pick is a median 0.003 below the best node on test** (mean 0.004, at most 0.017 on C1 seed 3).
- **The top-3 hedge (C3) gains 0.0004 on average,** at most 0.005.
- **The pick's test is within 0.018 of its validation on every run,** and A1-off never leaked (gap −0.001 to +0.017).

### 4. Cost and cut-off calls

- **$8.70 for the 21 runs,** about $0.41 a run.
- **75 of 2,290 calls were cut off** at the 64k-token cap (3.3%), between 0 and 70 minutes a run. Seed 0 still used StreamLake, so its runs were slower (51 to 86 nodes, against 35 to 200 later).

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C5 seed 4 | [C5-seed4.png](round5/trajectories/C5-seed4.png) | [C5-seed4.md](round5/trajectories/C5-seed4.md) |

## Files

- **`round5/grades/`:** MLE-bench's grade of the run.
- **`round5/trajectories/`:** its chart and timeline.
- **On Nabil's Mac only:** all 21 run folders, in `runs/kaggle/*_detecting-insults-in-social-commentary_seed*/`.

## Next

Insults' full plan is done. Its C6 live session, on the Mac, is still to run.
