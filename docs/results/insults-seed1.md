# Insults, seed 1: Kaggle round 2

2 Nov 2026, on Kaggle. Seed 1 of all five conditions on `detecting-insults-in-social-commentary`, round 2 of this task's full plan (`configs/kaggle_sessions.yaml`). Seed 0 is in [`insults-seed0.md`](insults-seed0.md). Pizza's half of the same sessions is on the `result-pizza` branch.

Insults is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.7784, bronze 0.7911, silver 0.8231, gold 0.8332.

## Setup

- **The same as seed 0** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours), with two changes:
  - **StreamLake excluded** from the LLM routing (`df79ace`), after it cut off 9% of its calls in round 1;
  - **`machine.jsonl` now says `kaggle`** (`b3c8ecf`).
- **Code:** `df79ace` on main.
- **Times (SGT):** 09:34 to about 13:35, sessions 6 to 10.
- **Cost:** about $2.88 for the five runs, more than twice seed 0's $1.23 (finding 2).
- **Health:** A1-off restarted once, after about 2.7 hours; `cloud_run.py` resumed it from its last checkpoint. A4-off stopped at the 200-node cap (`max_nodes`) after 3.9 hours, just before its budget ran out.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|
| C1 | 75 | **0.9058 (gold)** | n55: 0.9043 / 0.9303 | 0.9076 | 0.9058 | 13 |
| C4 | 150 | **0.9043 (gold)** | n138: 0.9017 / 0.9226 | 0.9082 | 0.9043 | 32 |
| C5 | 138 | **0.9115 (gold)** | n88: 0.9142 / 0.9254 | 0.9139 | 0.9123 | 4 |
| A1-off | 118 | **0.9021 (gold)** | n115: 0.9192 / 0.9156 | 0.9073 | 0.9072 | 20 |
| A4-off | 200 | **0.9126 (gold)** | n199: 0.9108 / 0.9267 | 0.9127 | 0.9127 | 20 |

- **Every run is gold again,** within 0.011 of each other.
- **No interventions:** neither C4 nor C5 fired. The C4 rule, replayed on the other runs (`scripts/replay_policy.py`), doesn't fire either.
- **The pick is 0.000 to 0.005 below the best node on test.**

## Findings

### 1. Two seeds: every condition is gold, within 0.008 on average

| Condition | Seed 0 | Seed 1 | Mean |
|---|---|---|---|
| C1 | 0.9021 | 0.9058 | 0.9040 |
| C4 | 0.9041 | 0.9043 | 0.9042 |
| C5 | 0.9004 | 0.9115 | 0.9060 |
| A1-off | 0.9037 | 0.9021 | 0.9029 |
| A4-off | 0.9083 | 0.9126 | **0.9105** |

- **The means are within 0.008,** while C5 alone moves 0.011 between its two seeds.
- **All 10 runs have gold,** so medal rates can't separate the conditions on insults.
- **A4-off has the best score on both seeds,** by 0.004 and 0.001. Two seeds aren't enough to say that's more than noise.

### 2. The new providers doubled the search, and the cost

With StreamLake excluded, most calls went to CoreWeave, which answers in about 1 minute against StreamLake's 2.5.
- **Runs made 75 to 200 nodes,** against 51 to 86 on seed 0.
- **The cost rose from $1.23 to $2.88** for the five runs, because more nodes means more calls.
- **Cut-off calls fell but didn't stop:** CoreWeave also cut off about 5% of its calls. Over both tasks and both rounds, Baidu, DeepInfra and BaseTen cut off none of their 311 calls.

So seed 0 and seed 1 ran at different speeds. Within a seed the conditions are compared fairly; across seeds the difference adds to the noise.

### 3. The probe is still easier than validation

As on seed 0, in the four runs with A1, the median node's probe is 0.019 to 0.029 above its validation, and test sits between them. A1-off, with its own validation split, has a gap of 0.005.

### 4. A1-off didn't leak

A1-off's pick has validation 0.919 against test 0.902, a gap of 0.017; on seed 0 it was 0.015. Neither seed has the kind of leak spooky's A1-off seed 1 had (0.256).

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 | [C1.png](insults-seed1/trajectories/C1.png) | [C1.md](insults-seed1/trajectories/C1.md) |
| C4 | [C4.png](insults-seed1/trajectories/C4.png) | [C4.md](insults-seed1/trajectories/C4.md) |
| C5 | [C5.png](insults-seed1/trajectories/C5.png) | [C5.md](insults-seed1/trajectories/C5.md) |
| A1-off | [A1-off.png](insults-seed1/trajectories/A1-off.png) | [A1-off.md](insults-seed1/trajectories/A1-off.md) |
| A4-off | [A4-off.png](insults-seed1/trajectories/A4-off.png) | [A4-off.md](insults-seed1/trajectories/A4-off.md) |

## Files

- **`insults-seed1/grades/`:** MLE-bench's grade of each run.
- **`insults-seed1/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders, in `runs/kaggle/*_detecting-insults-in-social-commentary_seed1/`.

## Next

Round 3 (sessions 11 to 15) runs seed 2 of every condition, with the same routing as this round.
