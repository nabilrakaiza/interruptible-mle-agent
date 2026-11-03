# Insults, seed 2: Kaggle round 3

2 to 3 Nov 2026, on Kaggle. Seed 2 of all five conditions on `detecting-insults-in-social-commentary`, round 3 of this task's full plan (`configs/kaggle_sessions.yaml`). Seeds 0 and 1 are in [`insults-seed0.md`](insults-seed0.md) and [`insults-seed1.md`](insults-seed1.md). Pizza's half of the same sessions is on the `result-pizza` branch.

Insults is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.7784, bronze 0.7911, silver 0.8231, gold 0.8332.

## Setup

- **The same as seed 1** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours, StreamLake excluded).
- **Code:** `30b2f95` on main. The only change since seed 1 is in `kaggle_collect.py` (downloads), not in the agent.
- **Times (SGT):** 22:08 to 02:09, sessions 11 to 15.
- **Cost:** about $2.16 for the five runs ($2.88 on seed 1).
- **Health:** no restarts. Every run stopped on its 4-hour budget.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|
| C1 | 81 | **0.9059 (gold)** | n58: 0.9032 / 0.9125 | 0.9084 | 0.9059 | 0 |
| C4 | 117 | **0.9098 (gold)** | n115: 0.9142 / 0.9367 | 0.9115 | 0.9098 | 16 |
| C5 | 82 | **0.9157 (gold)** | n74: 0.9069 / 0.9305 | 0.9157 | 0.9157 | 21 |
| A1-off | 74 | **0.9127 (gold)** | n65: 0.9118 / 0.9263 | 0.9143 | 0.9127 | 18 |
| A4-off | 129 | **0.9111 (gold)** | n75: 0.9139 / 0.9343 | 0.9133 | 0.9111 | 45 |

- **Every run is gold again,** within 0.010 of each other. C5's 0.9157 is the best insults run so far.
- **No interventions:** neither C4 nor C5 fired. The C4 rule, replayed on the other runs (`scripts/replay_policy.py`), doesn't fire either.
- **The pick is 0.000 to 0.003 below the best node on test.** C5 picked its best node.

## Findings

### 1. Three seeds: 15 golds, and the means are within 0.006

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.9021 | 0.9058 | 0.9059 | 0.9046 |
| C4 | 0.9041 | 0.9043 | 0.9098 | 0.9061 |
| C5 | 0.9004 | 0.9115 | **0.9157** | 0.9092 |
| A1-off | 0.9037 | 0.9021 | 0.9127 | 0.9062 |
| A4-off | 0.9083 | 0.9126 | 0.9111 | **0.9107** |

- **The means are within 0.006,** while C5 alone moves 0.015 across its three seeds.
- **All 15 runs have gold,** so medal rates can't separate the conditions on insults.
- **A4-off still has the best mean,** and C1 the lowest. With every interval this wide, neither is more than noise yet.

### 2. Cut-off calls: about 3%, as before

17 of the 542 calls were cut off at the 64k-token cap (3.1%), against 2.5% on seed 1 and 2.8% on seed 0. A4-off lost the most, 45 minutes over 8 calls, and still made 129 nodes.

### 3. The probe is still easier than validation

In the four runs with A1, the median node's probe is 0.012 to 0.027 above its validation, and the picks' test is close to validation (−0.004 to +0.009). The probe stays the optimistic one on insults, as on seeds 0 and 1.

### 4. A1-off didn't leak

A1-off's pick has validation 0.912 against test 0.913. Over three seeds the gap is 0.015, 0.017 and −0.001, never close to spooky's A1-off seed 1 leak.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 | [C1.png](insults-seed2/trajectories/C1.png) | [C1.md](insults-seed2/trajectories/C1.md) |
| C4 | [C4.png](insults-seed2/trajectories/C4.png) | [C4.md](insults-seed2/trajectories/C4.md) |
| C5 | [C5.png](insults-seed2/trajectories/C5.png) | [C5.md](insults-seed2/trajectories/C5.md) |
| A1-off | [A1-off.png](insults-seed2/trajectories/A1-off.png) | [A1-off.md](insults-seed2/trajectories/A1-off.md) |
| A4-off | [A4-off.png](insults-seed2/trajectories/A4-off.png) | [A4-off.md](insults-seed2/trajectories/A4-off.md) |

## Files

- **`insults-seed2/grades/`:** MLE-bench's grade of each run.
- **`insults-seed2/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders, in `runs/kaggle/*_detecting-insults-in-social-commentary_seed2/`.

## Next

The ablations are done (seeds 0 to 2). Round 4 (sessions 16 to 18, and 19 and 20) runs C1, C4 and C5 seed 3 and C1 and C4 seed 4; round 5 (session 21) is C5 seed 4.
