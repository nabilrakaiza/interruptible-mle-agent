# Pizza, round 4: C1, C4 and C5 seed 3, C1 and C4 seed 4

3 Nov 2026, on Kaggle. Sessions 16 to 20 of this task's full plan (`configs/kaggle_sessions.yaml`): seed 3 of C1, C4 and C5, and seed 4 of C1 and C4. The ablations finished at seed 2 ([`pizza-seed2.md`](pizza-seed2.md)). C5 seed 4 is round 5. Insults' half of the same sessions is on the `result-insults` branch.

Pizza is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.5996, bronze 0.6921, silver 0.7648, gold 0.9791. Validation has 576 rows and the probe 288.

## Setup

- **The same as seeds 1 and 2** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours, StreamLake excluded).
- **Code:** `30b2f95` on main, as in round 3.
- **Times (SGT):** 14:06 to 18:19, sessions 16 to 20, after each session's insults run.
- **Cost:** about $2.70 for the five runs.
- **Health:** no restarts. Every run stopped on its 4-hour budget.

## Results

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Interventions | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|---|
| C1 seed 3 | 100 | **0.7013 (bronze)** | n98: 0.7123 / 0.6873 | 0.7034 | 0.7013 | – | 14 |
| C4 seed 3 | 83 | **0.7060 (bronze)** | n80: 0.7135 / 0.6775 | 0.7162 | 0.7136 | none fired | 42 |
| C5 seed 3 | 109 | **0.6907** | n74: 0.7181 / 0.6824 | 0.6935 | 0.6907 | 2 corrections | 34 |
| C1 seed 4 | 80 | **0.7007 (bronze)** | n29: 0.7151 / 0.6838 | 0.7027 | 0.7007 | – | 60 |
| C4 seed 4 | 111 | **0.6671** | n15: 0.6936 / 0.7058 | 0.6839 | 0.6671 | **2 prunes** | 54 |

- **Three of five runs got bronze:** both C1 runs and C4 seed 3. C5 seed 3 missed by 0.001.
- **The pick is 0.002 to 0.017 below the best node on test,** and test is below validation for every pick (by 0.008 to 0.028), as in every pizza round.

## Findings

### 1. All seeds so far: C1 has 4 bronzes of 5

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean | Bronzes |
|---|---|---|---|---|---|---|---|
| C1 | 0.6842 | 0.6932 (b) | 0.7095 (b) | **0.7013 (b)** | **0.7007 (b)** | **0.6978** | **4 of 5** |
| C4 | 0.6692 | 0.7060 (b) | 0.6771 | **0.7060 (b)** | **0.6671** | 0.6851 | 2 of 5 |
| C5 | 0.7008 (b) | 0.6753 | 0.6829 | **0.6907** | round 5 | 0.6874 | 1 of 4 |
| A1-off | 0.6700 | 0.6954 (b) | 0.6899 | – | – | 0.6851 | 1 of 3 |
| A4-off | 0.6553 | 0.7078 (b) | 0.6822 | – | – | 0.6818 | 1 of 3 |

- **C1 leads on mean by 0.010** and has the most bronzes: 4 of 5, against 5 of 15 for the other four conditions together.
- **That's suggestive, not settled:** each condition's own range (0.025 for C1, 0.039 for C4, 0.053 for A4-off) is wider than the gaps between means, and the bronze line (0.692) sits in the middle of where pizza runs land.

### 2. C4 pruned live for the first time on pizza, and it didn't change the pick

On seed 4, C4 fired twice: after n54 it pruned n51's subtree (4 nodes), and after n72 n57's (14 nodes). In both, validation had risen since n50 while the probe fell (+1.0% against −4.7%, and +3.0% against −6.7%).
- **Neither prune touched the pick.** The pick, n15, came from step 15, and no later node beat its validation. The pruned subtrees' best validation was 0.666 and 0.677, against n15's 0.694.
- **The pruned branches weren't the good ones either:** their best test scores were 0.662 and 0.680.
- **The run's loss was in the pick, not the prunes:** n15 had validation 0.694 and test 0.667, while the best node on test, n105 (0.684), sat at 0.661 on validation.

### 3. C5 deleted a finding that test says was right, and the agent went back to it

C5 seed 3 made two corrections:
- **At step 45,** it deleted "histogram gradient boosting hurt validation in two attempts". The check failed because n20's probe went up slightly (+0.001) while its validation fell 0.032. Test sides with the finding: n20 scored 0.677 against its parent's 0.686.
- **At step 106,** it deleted a note about fixing a stacking bug, because its cited node, n100, had crashed. That one was harmless.

**After the first deletion, the agent used gradient boosting in 7 more nodes,** against 4 before. None beat the pick, so it cost search time rather than score. Across pizza's C5 runs, this is the second correction in a row that deleted a finding test agrees with (see seed 2). With a 288-row probe, the rule's "failed to replicate" check mostly reacts to noise.

### 4. The C4 rule, replayed, fires on three runs and never helps

Replayed on the C1 and C5 runs (`scripts/replay_policy.py`):
- **C1 seed 3:** fires twice (after n15 and n81); the pick stays n98.
- **C5 seed 3:** fires after n22; the pick becomes n13, and test **falls** from 0.691 to 0.686.
- **C1 seed 4:** fires after n25; the pick becomes n28, and test falls from 0.701 to 0.700.

Together with seeds 1 and 2, the replayed rule has now fired on 6 pizza runs: it helped once (by 0.004), changed nothing twice and hurt three times.

### 5. Cut-off calls are back to about 6%

33 of the 563 calls were cut off at the 64k-token cap (5.9%), against 0.3% in round 3 and 6.0% on seed 1. The routing is the same; the providers it lands on vary from day to day. C1 seed 4 lost the most, 60 minutes, and still got bronze.

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C1 seed 3 | [C1-seed3.png](pizza-round4/trajectories/C1-seed3.png) | [C1-seed3.md](pizza-round4/trajectories/C1-seed3.md) |
| C4 seed 3 | [C4-seed3.png](pizza-round4/trajectories/C4-seed3.png) | [C4-seed3.md](pizza-round4/trajectories/C4-seed3.md) |
| C5 seed 3 | [C5-seed3.png](pizza-round4/trajectories/C5-seed3.png) | [C5-seed3.md](pizza-round4/trajectories/C5-seed3.md) |
| C1 seed 4 | [C1-seed4.png](pizza-round4/trajectories/C1-seed4.png) | [C1-seed4.md](pizza-round4/trajectories/C1-seed4.md) |
| C4 seed 4 | [C4-seed4.png](pizza-round4/trajectories/C4-seed4.png) | [C4-seed4.md](pizza-round4/trajectories/C4-seed4.md) |

## Files

- **`pizza-round4/grades/`:** MLE-bench's grade of each run.
- **`pizza-round4/trajectories/`:** the chart and timeline of each run.
- **On Nabil's Mac only:** the run folders, in `runs/kaggle/*_random-acts-of-pizza_seed3/` and `..._seed4/`.

## Next

Round 5 (session 21, `imle-slot-1`) runs C5 seed 4, the last run of pizza's full plan.
