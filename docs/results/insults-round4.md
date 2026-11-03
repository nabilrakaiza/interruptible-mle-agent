# Insults, round 4: C1, C4 and C5 seed 3, C1 and C4 seed 4

3 Nov 2026, on Kaggle. Sessions 16 to 20 of this task's full plan (`configs/kaggle_sessions.yaml`): seed 3 of C1, C4 and C5, and seed 4 of C1 and C4. The ablations finished at seed 2 ([`insults-seed2.md`](insults-seed2.md)). C5 seed 4 is round 5. Pizza's half of the same sessions is on the `result-pizza` branch.

Insults is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.7784, bronze 0.7911, silver 0.8231, gold 0.8332.

## Setup

- **The same as seeds 1 and 2** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours, StreamLake excluded).
- **Code:** `30b2f95` on main, as in round 3.
- **Times (SGT):** 10:05 to 14:18, sessions 16 to 20.
- **Cost:** about $1.97 for the five runs.
- **Health:** no restarts. Every run stopped on its 4-hour budget.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|
| C1 seed 3 | 63 | **0.8928 (gold)** | n61: 0.9037 / 0.9303 | 0.9094 | 0.8928 | 70 |
| C4 seed 3 | 108 | **0.9083 (gold)** | n84: 0.9111 / 0.9224 | 0.9087 | 0.9083 | 34 |
| C5 seed 3 | 35 | **0.9020 (gold)** | n33: 0.9035 / 0.9268 | 0.9069 | 0.9040 | 26 |
| C1 seed 4 | 104 | **0.9030 (gold)** | n90: 0.9053 / 0.9224 | 0.9067 | 0.9030 | 32 |
| C4 seed 4 | 80 | **0.9007 (gold)** | n78: 0.8991 / 0.9217 | 0.9059 | 0.9008 | 49 |

- **Every run is gold again.**
- **No interventions:** neither C4 nor C5 fired. The C4 rule, replayed on the C1 and C5 runs (`scripts/replay_policy.py`), doesn't fire either.
- **The pick is 0.000 to 0.017 below the best node on test.** The 0.017 is C1 seed 3 (finding 2).

## Findings

### 1. All seeds so far: 25 golds, and the means are within 0.009

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean |
|---|---|---|---|---|---|---|
| C1 | 0.9021 | 0.9058 | 0.9059 | **0.8928** | **0.9030** | 0.9019 |
| C4 | 0.9041 | 0.9043 | 0.9098 | **0.9083** | **0.9007** | 0.9054 |
| C5 | 0.9004 | 0.9115 | 0.9157 | **0.9020** | round 5 | 0.9074 |
| A1-off | 0.9037 | 0.9021 | 0.9127 | – | – | 0.9062 |
| A4-off | 0.9083 | 0.9126 | 0.9111 | – | – | **0.9107** |

- **The means are within 0.009,** from C1's 0.9019 to A4-off's 0.9107. C5 alone ranges over 0.015 across its seeds, and C1 over 0.013.
- **All 25 runs have gold,** so medal rates can't separate the conditions on insults.
- **C1 now has the lowest mean,** mostly because of seed 3 (0.8928), the lowest insults run so far.

### 2. C1 seed 3 picked a node 0.017 below its best

C1 seed 3's pick, n61, had validation 0.904 but test 0.893. Its best node on test scored 0.909. That's the largest pick loss on insults so far; elsewhere it's about 0.005 or less.
- **The run also lost the most time:** 8 cut-off calls cost it 70 minutes, and it made only 63 nodes.
- **The top-3 hedge (C3) didn't help,** since the other two of its top 3 were no better on test.

### 3. Cut-off calls are back up to about 5%

25 of the 458 calls were cut off at the 64k-token cap (5.5%), against 3.1% in round 3 and 2.5% on seed 1. The routing is the same; the providers it lands on vary from day to day. Every run lost between 26 and 70 minutes to them.

### 4. C5 seed 3 made only 35 nodes

Its scripts took a median 4.5 minutes each, against 1.6 to 2.6 minutes in the other four runs this round, and it still reached gold at 0.902. More nodes don't buy much on insults: the 35-node run is within 0.006 of the 108-node one.

### 5. The probe is still easier than validation

The median node's probe is 0.020 to 0.031 above its validation in all five runs, and the picks' test sits within 0.011 of validation, as in every round before.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 seed 3 | [C1-seed3.png](insults-round4/trajectories/C1-seed3.png) | [C1-seed3.md](insults-round4/trajectories/C1-seed3.md) |
| C4 seed 3 | [C4-seed3.png](insults-round4/trajectories/C4-seed3.png) | [C4-seed3.md](insults-round4/trajectories/C4-seed3.md) |
| C5 seed 3 | [C5-seed3.png](insults-round4/trajectories/C5-seed3.png) | [C5-seed3.md](insults-round4/trajectories/C5-seed3.md) |
| C1 seed 4 | [C1-seed4.png](insults-round4/trajectories/C1-seed4.png) | [C1-seed4.md](insults-round4/trajectories/C1-seed4.md) |
| C4 seed 4 | [C4-seed4.png](insults-round4/trajectories/C4-seed4.png) | [C4-seed4.md](insults-round4/trajectories/C4-seed4.md) |

## Files

- **`insults-round4/grades/`:** MLE-bench's grade of each run.
- **`insults-round4/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders, in `runs/kaggle/*_detecting-insults-in-social-commentary_seed3/` and `..._seed4/`.

## Next

Round 5 (session 21, `imle-slot-1`) runs C5 seed 4, the last run of insults' full plan.
