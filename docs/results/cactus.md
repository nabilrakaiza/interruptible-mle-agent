# Cactus: all results of the half plan

The half plan's 13 runs on `aerial-cactus-identification`: seeds 0, 1 and 2 of C1, C4 and C5, and seeds 0 and 1 of A1-off and A4-off. They ran from 26 to 28 Oct 2026 on Dziand's Mac. Each seed has its own write-up:

- [`cactus-seed0.md`](cactus-seed0.md): all five conditions, seed 0
- [`cactus-seed1.md`](cactus-seed1.md): all five conditions, seed 1
- [`cactus-seed2.md`](cactus-seed2.md): C1, C4 and C5, seed 2
- [`cactus-c6.md`](cactus-c6.md): the C6 live session, seed 101, and the unwatched C6 run on seed 100

Cactus is ROC AUC, so **higher is better**. MLE-bench thresholds: median 0.9991, and bronze, silver and gold are all 1.0.

## Setup

- DeepSeek V4 Flash 0731 (fp8), Docker sandbox, 2 hours and 2 CPUs per run, A1 on unless the condition turns it off.
- **Machine:** a 13-inch MacBook Pro (2022, Apple M2, 8 cores, 8 GB of memory), macOS 14.1.1. Docker ran in Colima (conda-forge build) with a 2-CPU, 5 GB VM, and each script's sandbox was capped at 2 CPUs and 4 GB inside it. **Training was on CPU only:** Docker on macOS can't reach the M2's GPU, and no script asked for CUDA or MPS. Runs went one at a time, with the laptop on power. Each run records its machine in `machine.jsonl`.
- Every run with the PR #7 fix for `OUTPUT_DIR` statements (`main` at 92cff79).
- **Cost:** $1.12 for the 13 runs ($0.249, $0.397 and $0.479 a seed), plus $0.018 for the smoke run and $0.247 for the two C6 runs ($0.095 on seed 100, $0.152 on seed 101).
- **Health:** no restarts, and 0 failed LLM calls out of 475. Every run finished on its budget and made a valid submission. The same holds for both C6 runs (0 failed calls out of 74).

## Test scores

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.99977 | 0.99994 | 0.99917 | 0.99963 |
| C2 (oracle, from C1) | 0.99982 | 0.99994 | 0.99942 | **0.99973** |
| C3 (top 3, from C1) | 0.99977 | 0.99994 | 0.99929 | 0.99967 |
| C4 | 0.99936 | 0.99992 | 0.99979 | 0.99969 |
| C5 | 0.99999 | 0.99927 | 0.99984 | 0.99970 |
| A1-off | 0.99972 | 0.99993 | n/a | 0.99982 |
| A4-off | 0.99961 | 0.99940 | n/a | 0.99950 |

- **All 13 runs are valid and above the median. None medalled.** Every medal threshold is 1.0, a perfect AUC, and no node in any run reached it. The closest was C5 seed 0 (0.99999).
- **C2 beats C1 on two seeds out of three,** by 0.00005 (seed 0) and 0.00025 (seed 2). C3 recovers none of the first and half of the second.
- **No condition is clearly better than another.** C1 alone ranges over 0.0008 across seeds, more than the gap between any two conditions' means (at most 0.0003). The full table with bootstrap intervals is in [`cactus-seed2/outcomes/summary.md`](cactus-seed2/outcomes/summary.md).

## Interventions

| Runs | Fired | Effect on the submission |
|---|---|---|
| C4, seeds 0 to 2 | never | none |
| C5, seeds 0 to 2 | never | none |
| C4 rule replayed on all 13 runs | never | none |
| C5 rule replayed on all 13 runs | twice (C1 seed 0 after n34; A1-off seed 1 after n24) | none |

- **Neither C4 nor C5 fired in a live run,** and no run wrote a `queue.jsonl`. C4 and C5's runs are therefore C1's agent on other random paths.
- **Replayed after the run** (`scripts/replay_policy.py`), C4's rule fires nowhere, not even on A1-off, where spooky's leak made it fire. C5's rule fires twice, in runs that are not C5, each time on a finding that cites a node which crashed. Deleting those findings would have changed no pick.

## C6 live session

One session, seed 101, oversight only, with an AI assistant that suggested the interventions ([`cactus-c6.md`](cactus-c6.md)). Test **0.99953**, 0.00003 from the run's best node, within C1's seed range and below its mean.

- **8 interventions, all prunes:** the four non-CNN drafts, two regressions, a crashed node and a weak branch. None of the 16 pruned nodes beat the pick on test, and none changed it.
- **The C4 rule:** replayed over the session, it fires 0 times; validation and probe never diverged. All 8 prunes followed cues the rule doesn't have: wrong model family, a branch far behind, little time left.
- **Prunes act late, and choose only where the search doesn't go:** two prunes applied after the nodes they meant to stop had run, and after the last one the search spent 25 minutes rebuilding n7 and n8 from another weak node.
- **The unwatched C6 run on seed 100** (0 interventions) scored 0.99989, first on test of its 29 working nodes.

## Main findings

1. **Cactus is at the ceiling.** Every run passed 0.999 on test within its first 26 nodes, and from there the search moves only the fourth decimal. Medals need a perfect score, so "any medal" is 0% for every condition by construction.
2. **Without A1, nothing leaked.** The picks' validation and test stayed within 0.0004 in every run, A1-off included (+0.00018 on seed 0, −0.00010 on seed 1). Over all working nodes, A1-off's mean gap (+0.0005 to +0.0010) is the same size as C1's (+0.0005 to +0.0007). Spooky's A1-off drifted 0.132 on seed 1; with every model near 0.999 AUC, fitting to one's own split has nothing to gain here.
3. **Interventions had no work on cactus.** With A1 on, and with it off, validation and probe moved together and the agent's findings replicated, so the monitors stayed silent. This matches spooky's lesson from the other side: interventions only have work when the agent's own signal breaks, and on cactus it never did.
4. **Final selection barely matters.** Across all 13 runs, the oracle pick would have gained at most 0.00029 (C4 seed 0, where C3 recovers all of it) and 0.00025 in C1 seed 2. In eleven runs, the pick is first on test or within 0.0001 of it.
5. **The leakage check never fired.** Unlike spooky's C1 seed 2, no cactus script was stopped for evaluating on rows it was fitted on.
6. **Seed noise dominates,** at about 0.0008 within a condition, against gaps of at most 0.0003 between conditions.
7. **A person at the dashboard had only waste to prune.** C6's 8 prunes removed branches far behind or regressions, cost nothing on test and changed no pick ([`cactus-c6.md`](cactus-c6.md)). On spooky, the person's prunes included one real divergence; on cactus there was none to find.

## Pick's validation against test

AUC is higher-is-better, so a positive gap here means validation was optimistic, the same sense as a positive gap on spooky.

| Run | Validation | Test | Gap (validation − test) |
|---|---|---|---|
| C1 seed 0 | 0.99984 | 0.99977 | +0.00007 |
| C1 seed 1 | 0.99989 | 0.99994 | −0.00005 |
| C1 seed 2 | 0.99912 | 0.99917 | −0.00005 |
| C4 seed 0 | 0.99962 | 0.99936 | +0.00026 |
| C4 seed 1 | 0.99998 | 0.99992 | +0.00006 |
| C4 seed 2 | 0.99958 | 0.99979 | −0.00021 |
| C5 seed 0 | 0.99999 | 0.99999 | 0.00000 |
| C5 seed 1 | 0.99931 | 0.99927 | +0.00004 |
| C5 seed 2 | 0.99991 | 0.99984 | +0.00007 |
| A4-off seed 0 | 0.99983 | 0.99961 | +0.00022 |
| A4-off seed 1 | 0.99978 | 0.99940 | +0.00038 |
| **A1-off seed 0** | 0.99990 | 0.99972 | +0.00018 |
| **A1-off seed 1** | 0.99983 | 0.99993 | −0.00010 |
| C6 seed 100 (unwatched) | 0.99985 | 0.99989 | −0.00004 |
| C6 seed 101 | 0.99965 | 0.99953 | +0.00012 |

## Limitations

- **A ceiling task.** With every model near 0.999 and medals only at 1.0, cactus can't separate conditions by score, and medal rates are uninformative.
- Few seeds, and 2-hour runs on 2 CPUs with a 4 GB sandbox limit. One A1-off node was killed for running out of memory.
- One model, and no pretrained models offline. The agent trains CNNs from scratch, or uses scikit-learn on raw pixels.
- The C4 and C5 thresholds are the same as on spooky, set from a handful of pilots. Cactus never came close to them.
- **C6 is one watched session with an adviser.** The assistant suggested every intervention, so the session measures a person with an AI adviser, not a person alone, and can't be compared directly with spooky's session. It ran on seed 101 because seed 100's C6 run was not watched.
- **Cactus is public.** It is an old Kaggle competition, so its winning approaches are online and may be in the model's training data. The C6 participant did not search online, to stay in the same position as the offline agent.

## Next

- **For the slides:** cactus is the control task. Every condition lands within 0.0008 of a perfect score, no scripted monitor intervenes, a person at the dashboard finds only waste to prune, and A1-off does not leak. Against spooky's A1-off seed 1, it shows that A1 and the interventions matter where the agent's own signal can mislead it, not everywhere.
