# Pizza, C6 at 4 hours: Claude as the monitor

12 Nov 2026, 13:04 to 17:04, Dziand's Mac. One C6 run on `random-acts-of-pizza`, seed 100, with a 4 hour budget to match Nabil's 21-run pizza grid (`docs/results/analysis/pizza.md` on the `result-pizza` branch). **Every intervention was made by Claude (Opus 5.5), not by a person.** The participant was busy, so Claude acted as the monitor, checking about every 15 minutes. The notes are in [`pizza-c6-4h/c6_notes.md`](pizza-c6-4h/c6_notes.md).

Pizza is ROC AUC, so **higher is better**. MLE-bench thresholds: median 0.5996, bronze 0.6921, silver 0.7648, gold 0.9791.

## Result

| | Validation | Probe | **Test** |
|---|---|---|---|
| **n101 (submitted)** | 0.7153 | 0.6858 | **0.66711**: 94th of 123 scored nodes |
| C3 (best of the top 3 by validation: n69) | 0.7135 | 0.6917 | 0.67433 |
| C2 among nodes Claude didn't prune (n16) | 0.6912 | 0.6720 | 0.68232 |
| C2 over every node (n15, pruned by Claude) | 0.6760 | 0.6905 | 0.69229, just above bronze |
| C4 rule, replayed (picks n12) | 0.6814 | 0.6984 | 0.67947 |

- **Valid and above the median, no medal.**
- **This is a poor result.** Against Nabil's grid it is below all 5 C1 seeds (0.684 to 0.709, mean 0.698), and tied with the grid's worst C4 run (C4 seed 4, also 0.66711). Only A4-off seed 0 (0.6553) is lower.
- **The pick overfitted validation:** validation − test is +0.048, larger than any of Nabil's C1 runs (+0.011 to +0.040), and the probe (0.686) had already dropped 0.03 below validation.
- **Claude's pruning made it worse,** as the next sections show. The best node on test, and 68 of the other 92 that beat the pick, were pruned by Claude.

## Setup

- **Run:** `c6_live.yaml` (`monitors: [human]`), 4 hours, DeepSeek V4 Flash 0731, A1, `--retries 0`, seed 100.
- **Machine: not the same as Nabil's.** His grid ran on Kaggle CPU with the subprocess sandbox and 2 threads. This run was on a 13-inch MacBook Pro (Apple M2, 8 cores, 8 GB; `machine.jsonl`: arm64, 8 CPUs, 8.6 GB), with Docker in Colima (2-CPU, 5 GB VM), CPU only. Node speed and memory differ, so steps per hour aren't comparable with his runs.
- **Data:** prepared from the participant's Kaggle zip with MLE-bench's own functions. The zip's MD5 and the prepared `public/` and `private/` checksums all match MLE-bench's.
- **Power:** on battery 13:04 to about 14:20 (down to 78%), on AC 14:20 to about 15:20, then on battery to the end (89%). Disk dropped to 309 MB at 13:27 because macOS swap grew to 3.6 GB. Claude cleared package caches and, with the participant's OK, Chrome's cache, which brought it back to 4.6 GB. No node failed because of it.
- **Monitor:** Claude appended prune lines to `queue.jsonl` (`source: human`, every note starting `Claude:`) and checked `applied.jsonl` at the next check. It read validation and probe scores, plans and scripts, and **did not read test scores until the run had ended.** The participant opened the dashboard once (14:2x).
- **Cost:** $0.35, 141 LLM calls (0 failed), 126 nodes, 143 steps, 1 timeout.

## Two failed launches, and a harness bug

The run in this report is the third launch. The first two are in `runs/aborted/`:

1. **12:20, no Docker.** Claude launched from a shell without Colima's tools on `PATH`, so n0 crashed with `No such file or directory: 'docker'`. This was Claude's mistake, and nothing else was lost.
2. **12:23 to 12:40, every node invalid.** n0 and n1 both failed with `ids do not match predict.csv: 2027 rows, expected 2026`.
   - **The cause is in the harness, not the agent.** One post in MLE-bench's pizza `test.json` (and 4 in `train.json`) has a bare carriage return (`\r`) in `request_text_edit_aware`. `stand_in_evaluation.prepare` writes `predict.csv` with pandas' default quoting, which leaves a bare `\r` unquoted, and `pd.read_csv` then splits that post into two rows.
   - It doesn't depend on the seed (seeds 0 to 2 and 100 to 105 all fail), and it isn't the pandas version (2.2.3 and 3.1.0 behave the same).
   - It isn't clear why Nabil's Kaggle runs didn't hit it. Kaggle's copy of the data may differ (not checked).
   - Claude's notes on this launch are in [`pizza-c6-4h/aborted_crbug_notes.md`](pizza-c6-4h/aborted_crbug_notes.md).

**The fix**, in its own commit on this branch:
- `prepare` writes pizza's `train.csv` and `predict.csv` with `quoting=csv.QUOTE_NONNUMERIC`.
- On every row without a `\r`, the frames read back exactly as before (same values, same dtypes).
- `predict.csv` now has 2026 rows, matching the labels, and `train.csv` has 2014.
- Other tasks are unchanged, and `tests/test_stand_in_evaluation.py` passes.
- It touches shared code, so it should be reviewed before it goes anywhere near `main`.

## Interventions

**94 prunes queued, 79 applied, 15 dropped** (already pruned, because a prune removes the whole subtree). The first applied after 9 of 126 nodes (13:27). Every check found new nodes to prune.

Claude's criteria were carried over from cactus seeds 101 and 102: prune broken branches, clear regressions, duplicates and weak model families; keep the best lines; never prune the best node or its ancestors. In practice that meant:

| Reason (of 94 queued) | Prunes | Example |
|---|---|---|
| child below its parent on validation | 73 | n15: char n-gram SVD, 0.676 < parent n14 0.685 |
| duplicate (identical validation to 16 digits) or no effect | 14 | n80: the same change to n64 as n65 and n76, for the third time |
| weak model family, weak draft or superseded | 6 | n2, n8: the random forest line, 0.04 behind |
| fitted on held-out rows | 1 | n63: fitted its TF-IDF on `predict.csv` text |

Over the run the best validation score rose from 0.651 (n0) to 0.7153 (n101) through one line of gradient-boosted trees on TF-IDF, SVD and hand-made text features: n5 → n12 → n13 → n30 → n37 → n90 → n99 → n101.

## What the prunes did, judged on test afterwards

The pruning rule was wrong for this task.

- **"Below its parent on validation" was noise here.** Pizza's validation split has 576 rows, so differences of 0.01 to 0.02 AUC between a node and its parent are within noise. On cactus seed 102, Claude used a cutoff scaled to the task's noise. Here it pruned any child that scored lower, which on pizza amounts to pruning at random with respect to test.
- **It removed the nodes that generalised.** The top 4 nodes on test, n15 (0.692), n21 (0.688), n36 (0.684) and n78 (0.683), were all pruned as regressions. n15 alone would have reached bronze.
- **It pushed the search into validation-chasing.** Keeping only children that beat their parent on validation selects for nodes that fit the validation split. Along the final line, validation rose 0.715 − 0.681 = +0.034 from n12 to n101 while test fell 0.680 − 0.667 = −0.012.
- **The C4 rule would have done better.** Replayed with `scripts/replay_policy.py`, it fires once: after n30, it prunes n13's subtree because validation rose 1.0% while the probe fell 2.7% over 2 nodes. That subtree holds the line Claude kept and the final pick. C4's pick would have been n12, test 0.6795 (+0.012).

| | C4 prunes | C4 does not prune |
|---|---|---|
| **Claude prunes** | 0 | 79 |
| **Claude does not prune** | n13's subtree, which Claude kept as the best line | the rest |

## What the run suggests

1. **A monitor's pruning rule has to match the task's noise.** The same "child below parent" rule was harmless on cactus, where every node sits near 0.9999 and the validation split is large. On pizza it removed the best nodes on test. A monitor needs a noise estimate, such as the split size or the validation − probe gap, before treating a drop as a regression.
2. **The probe was the warning Claude didn't use.** Claude read probe scores but pruned on validation. The C4 rule, which uses validation − probe divergence, saw the overfitting at n30; Claude never did.
3. **Heavy pruning narrows the search to one line.** With 79 prunes, the search spent most of its 4 hours improving one gradient-boosting line, and its final steps kept rediscovering the same changes (n65, n76 and n80 are identical).
4. **Prunes cascade.** Pruning a node removes its whole subtree, and 15 of Claude's prunes were dropped because a parent had already gone. Claude avoided pruning the best node's ancestors for this reason.

## Limitations

- **The monitor was Claude, not a person.** This run measures an AI monitor applying criteria taken from a human's cactus session, not C6 as the protocol defines it.
- **No human debrief.** The participant asked for the report straight after the run, so nobody reviewed Claude's decisions before grading.
- **One run, seed 100,** against Nabil's 5 seeds per condition (seeds 0 to 4).
- **A different machine and sandbox** from the grid (Docker on an M2 Mac against Kaggle CPU with the subprocess sandbox).
- **The harness fix.** The run used a local fix to `stand_in_evaluation.py` that the grid didn't have. On rows without a `\r` the data are identical, but Nabil's runs were not affected by the bug for a reason that isn't known.
- **Claude checked every 15 minutes,** on a fixed schedule, and couldn't use the dashboard's views.
- `interaction_cost.py` reports 0 human minutes, because the prunes went into the queue directly, not from a dashboard session.
- Nabil's C4 seed 4 and this run both score exactly 0.6671091140093441 on test. AUC on 1162 rows takes a limited set of values, so this may be a coincidence. It was not investigated.

## Files

- **`pizza-c6-4h/c6_notes.md`:** Claude's notes, one section per check, with every decision and its reason.
- **`pizza-c6-4h/queue.jsonl`, `applied.jsonl`, `dashboard_log.jsonl`:** every intervention and dashboard event, with timestamps.
- **`pizza-c6-4h/grade.json`:** MLE-bench's grade.
- **`pizza-c6-4h/timeline.md`, `trajectory.png`:** the run's timeline and chart (`scripts/trajectory.py`).
- **`pizza-c6-4h/replay_policy.csv`, `replay_policy_interventions.csv`:** the C4 rule replayed over the run.
- **`pizza-c6-4h/interaction_cost.md`:** `scripts/interaction_cost.py`.
- **`pizza-c6-4h/aborted_crbug_notes.md`:** notes on the launch that hit the `\r` bug.
