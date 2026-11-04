# Pizza, round 5: C5 seed 4, and the full plan

4 Nov 2026, on Kaggle. Session 21, the last of this task's full plan (`configs/kaggle_sessions.yaml`): C5 seed 4. With it, pizza has all 21 runs. The earlier rounds are in [`pizza-seed0.md`](pizza-seed0.md), [`pizza-seed1.md`](pizza-seed1.md), [`pizza-seed2.md`](pizza-seed2.md) and [`pizza-round4.md`](pizza-round4.md). Insults' half of the session is on the `result-insults` branch.

Pizza is binary AUC, so **higher is better**. MLE-bench thresholds: median 0.5996, bronze 0.6921, silver 0.7648, gold 0.9791. Validation has 576 rows and the probe 288.

## Setup

- **The same as rounds 3 and 4** (Kaggle CPU, Python 3.13.6 with the sandbox image's packages, `--sandbox subprocess` capped at 2 threads, DeepSeek V4 Flash 0731 fp8, A1, 4 hours, StreamLake excluded).
- **Code:** `30b2f95` on main.
- **Times (SGT):** 03:37 to 07:39, in `imle-slot-1`, after the session's insults run.
- **Cost:** about $0.47.
- **Health:** no restarts. The run stopped on its 4-hour budget.

## Result

| Run | Nodes | **Test** | Pick: validation / probe | C2 (oracle) | C3 (top 3) | Interventions | Minutes lost to cut-off calls |
|---|---|---|---|---|---|---|---|
| C5 seed 4 | 95 | **0.6740** | n24: 0.7066 / 0.6694 | 0.6861 | 0.6861 | 3 corrections | 36 |

- **No medal,** 0.018 below bronze.
- **The pick lost 0.012 to a near-tie.** n24 had validation 0.7066 and test 0.674. n21 had validation 0.7055, only 0.001 lower, and test 0.686. No later node beat n24's validation. The top-3 hedge (C3) would have picked n21.
- **C5 deleted three findings, and test agrees with all three:**
  - "request-time temporal features help" (n6 against n0: validation +0.043, probe −0.009, test +0.015);
  - "fitting TF-IDF and SVD on train plus test hurts" (n22 against n21: validation −0.027, probe +0.004, test −0.034);
  - "removing stop words hurts" (n34 against n29: validation −0.057, probe +0.014, test −0.014).
- **The C4 rule, replayed (`scripts/replay_policy.py`), fires once,** after n54, prunes 16 nodes, and leaves the pick unchanged.

## The full plan: 21 runs

| Condition | Seed 0 | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean | Bronzes |
|---|---|---|---|---|---|---|---|
| C1 | 0.6842 | 0.6932 (b) | 0.7095 (b) | 0.7013 (b) | 0.7007 (b) | **0.6978** | **4 of 5** |
| C4 | 0.6692 | 0.7060 (b) | 0.6771 | 0.7060 (b) | 0.6671 | 0.6851 | 2 of 5 |
| C5 | 0.7008 (b) | 0.6753 | 0.6829 | 0.6907 | **0.6740** | 0.6847 | 1 of 5 |
| A1-off | 0.6700 | 0.6954 (b) | 0.6899 | – | – | 0.6851 | 1 of 3 |
| A4-off | 0.6553 | 0.7078 (b) | 0.6822 | – | – | 0.6818 | 1 of 3 |

### 1. C1 is the best condition on pizza, but not by a margin three to five seeds can confirm

- **C1 has the best mean (0.6978) and 4 bronzes in 5,** against 5 in 16 for the other four conditions together.
- **The gap to the next mean is 0.013,** while one condition's seeds range up to 0.053 (A4-off) and C4's over 0.039. The bronze line (0.692) sits in the middle of where pizza runs land.
- **C1 is also the steadiest** (SD 0.010, against 0.011 to 0.026 for the others).

### 2. The interventions fired on pizza, and didn't help

Pizza is the one task where both rules had work, because its small probe (288 rows) and validation (576) disagree often.
- **C4 pruned live 3 times, in 2 of its 5 runs** (seeds 0 and 4). No prune changed the pick.
- **The C4 rule, replayed on the C1, C5 and ablation runs, fired on 8 of them:** it improved the pick twice (by 0.006 and 0.004), changed nothing three times and made it worse three times (by up to 0.024).
- **C5 made 11 corrections in its 5 runs.** For seeds 2 to 4, we checked each against test: all 5 deleted findings that made a claim were right according to test, and the sixth was a harmless note about a crashed node. After one deletion (seed 3), the agent went back to a model the finding had warned against, 7 more times.
- **C5 has the lowest bronze rate of the five conditions,** 1 in 5.

C5's check reads "validation and probe moved in opposite directions" as "the finding didn't replicate". On a 288-row probe, that's usually noise: in 4 of the 5 cases checked, test sided with validation against the probe. In the fifth (seed 2), the check compared a different pair of nodes from the one the finding was about.

### 3. Picking by validation costs more on pizza than elsewhere

- **The pick is a median 0.009 below the best node on test** (mean 0.010, at most 0.035 on C4 seed 2), against 0.003 on insults.
- **The pick's test is below its validation on all but one run,** by 0.026 on average and up to 0.053. With 576 validation rows, the best validation score is partly luck.
- **The top-3 hedge (C3) gains 0.002 on average,** and up to 0.017 (C4 seed 2).

### 4. Cost and cut-off calls

- **$8.61 for the 21 runs,** about $0.41 a run.
- **112 of 2,170 calls were cut off** at the 64k-token cap (5.2%). Seed 0, which still used StreamLake, lost the most (C1 112 minutes of 240).

## Trajectories

| Run | Chart | Timeline |
|---|---|---|
| C5 seed 4 | [C5-seed4.png](pizza-round5/trajectories/C5-seed4.png) | [C5-seed4.md](pizza-round5/trajectories/C5-seed4.md) |

## Files

- **`pizza-round5/grades/`:** MLE-bench's grade of the run.
- **`pizza-round5/trajectories/`:** its chart and timeline.
- **On Nabil's Mac only:** all 21 run folders, in `runs/kaggle/*_random-acts-of-pizza_seed*/`.

## Next

Pizza's full plan is done. Its C6 live session, on the Mac, is still to run.
