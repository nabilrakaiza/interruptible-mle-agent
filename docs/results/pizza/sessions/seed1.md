# Pizza, seed 1: Kaggle round 2

2 Nov 2026, on Kaggle. Seed 1 of all five conditions on `random-acts-of-pizza`, round 2 of this task's full plan (`configs/kaggle_sessions.yaml`). Seed 0 is in [`seed0.md`](seed0.md). Insults' half of the same sessions is on the `result-insults` branch.

Pizza is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.5996, bronze 0.6921, silver 0.7648, gold 0.9791. Validation has 576 rows and the probe 288.

## Setup

- **The same as seed 0** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours), with two changes:
  - **StreamLake excluded** from the LLM routing (`df79ace`), after it cut off 9% of its calls in round 1;
  - **`machine.jsonl` now says `kaggle`** (`b3c8ecf`).
- **Code:** `df79ace` on main.
- **Times (SGT):** about 13:30 to 17:50, sessions 6 to 10.
- **Cost:** about $2.86 for the five runs, against $1.36 on seed 0 (finding 4).
- **Health:** no restarts.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Interventions | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|---|
| C1 | 134 | **0.6932 (bronze)** | n112: 0.7329 / 0.6947 | 0.7099 | 0.6959 | – | 23 |
| C4 | 79 | **0.7060 (bronze)** | n63: 0.7216 / 0.7008 | 0.7123 | 0.7061 | none fired | 69 |
| C5 | 116 | **0.6753** | n113: 0.6977 / 0.6995 | 0.6949 | 0.6798 | 3 corrections | 43 |
| A1-off | 113 | **0.6954 (bronze)** | n110: 0.7256 / 0.6781 | 0.6988 | 0.6955 | – | 10 |
| A4-off | 109 | **0.7078 (bronze)** | n79: 0.7070 / 0.6825 | 0.7078 | 0.7078 | – | 37 |

- **Four of five runs got bronze.** On seed 0 only C5 did. C5 is the one without a medal this time.
- **The pick is up to 0.020 below the best node on test** (C5), and 0.017 on C1. Picking by validation costs more on pizza than on insults or spooky.

## Findings

### 1. Two seeds: the conditions are within 0.007, and each has exactly one bronze

| Condition | Seed 0 | Seed 1 | Mean |
|---|---|---|---|
| C1 | 0.6842 | 0.6932 (bronze) | **0.6887** |
| C4 | 0.6692 | 0.7060 (bronze) | 0.6876 |
| C5 | 0.7008 (bronze) | 0.6753 | 0.6881 |
| A1-off | 0.6700 | 0.6954 (bronze) | 0.6827 |
| A4-off | 0.6553 | 0.7078 (bronze) | 0.6816 |

- **The means are within 0.007.** A single condition moves up to 0.053 between its two seeds (A4-off).
- **Every condition has one bronze in two seeds.** The bronze line (0.692) sits in the middle of where pizza runs land, so whether a run medals is close to a coin toss.

### 2. Validation is optimistic, and the pick suffers for it

On C1, the pick's validation is 0.733 but its test is 0.693; on A1-off, 0.726 against 0.695. With 576 validation rows, the node with the best validation is partly the luckiest one.
- **The best node on test was 0.017 better than C1's pick and 0.020 better than C5's.**
- **The top-3 hedge (C3) barely helps:** it gains 0.003 on C1 and 0.005 on C5.

### 3. C5 corrected three findings, and still missed the medal

C5 deleted three of the agent's findings, each because a cited node's probe moved the other way from its validation:
- n5 against n0: validation −0.013, probe +0.047;
- n25 against n22: validation +0.024, probe −0.013;
- n60 against n57: validation −0.006, probe +0.017.

Its pick, n113, scored 0.675, the lowest of the five. On seed 0, two corrections came before a bronze. Two runs can't show whether the corrections help on pizza; with a probe of 288 rows, many of these "failed to replicate" checks are likely noise.

### 4. The C4 rule didn't fire live, and replayed it's mixed

C4 itself never fired on seed 1. Replayed on the other runs (`scripts/replay_policy.py`), the rule fires on two:
- **C5:** at n27, pruning 73 nodes; the pick becomes n69 and test improves from 0.675 to 0.679.
- **A1-off:** at n74, pruning 98 nodes; the pick becomes n99 and test **falls** from 0.695 to 0.671.

On pizza, the probe is small enough that the rule's divergence check sometimes fires on noise.

### 5. The new providers doubled the search, and the cost

With StreamLake excluded, most calls went to CoreWeave, which answers about twice as fast.
- **Runs made 79 to 134 nodes,** against 28 to 64 on seed 0.
- **The cost rose from $1.36 to $2.86.**
- **Cut-off calls fell but didn't stop:** CoreWeave also cut off about 5% of its calls, costing C4 69 minutes.

So seed 0 and seed 1 ran at different speeds. Within a seed the conditions are compared fairly; across seeds the difference adds to the noise.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 | [C1.png](seed1/trajectories/C1.png) | [C1.md](seed1/trajectories/C1.md) |
| C4 | [C4.png](seed1/trajectories/C4.png) | [C4.md](seed1/trajectories/C4.md) |
| C5 | [C5.png](seed1/trajectories/C5.png) | [C5.md](seed1/trajectories/C5.md) |
| A1-off | [A1-off.png](seed1/trajectories/A1-off.png) | [A1-off.md](seed1/trajectories/A1-off.md) |
| A4-off | [A4-off.png](seed1/trajectories/A4-off.png) | [A4-off.md](seed1/trajectories/A4-off.md) |

## Files

- **`seed1/grades/`:** MLE-bench's grade of each run.
- **`seed1/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders, in `runs/kaggle/*_random-acts-of-pizza_seed1/`.

## Next

Round 3 (sessions 11 to 15) runs seed 2 of every condition, with the same routing as this round.
