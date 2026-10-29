# Findings of the half plan

All four tasks are complete: 13 grid runs each, and a live session on each.

| Task | Modality | Owner | Grid runs | C6 |
|---|---|---|---|---|
| **spooky** | text | Nabil | 13 of 13 | 1 session |
| **cactus** | image | Dziand | 13 of 13 | 1 session, plus 1 unwatched run |
| **nomad** | tabular | Sahi | 13 of 13 | 1 session |
| **leaf** | image + tabular | Medhini | 13 of 13 | 1 session |

Each task has its own write-up:
- [`spooky.md`](spooky.md), with [`spooky-c6.md`](spooky-c6.md) and [`spooky-drops.md`](spooky-drops.md)
- [`cactus.md`](cactus.md), with [`cactus-c6.md`](cactus-c6.md)
- [`nomad.md`](nomad.md), a summary of Sahi's package in [`nomad/`](nomad/README.md)
- [`leaf.md`](leaf.md), a summary of Medhini's package in [`leaf/`](leaf/findings.md)

## Setup

| | Spooky | Cactus | Nomad | Leaf |
|---|---|---|---|---|
| Metric | log loss ↓ | ROC AUC ↑ | RMSLE ↓ | log loss ↓ |
| Median / bronze | 0.4188 / 0.2938 | 0.9991 / 1.0 | 0.0699 / 0.0658 | 0.1083 / 0.0153 |
| Probe split | 1,762 rows | | ~216 rows | 89 rows (99 classes) |
| Machine | MacBook Pro M1, 8 GB | MacBook Pro M2, 8 GB | not recorded | not recorded |

All four used the same setup:
- DeepSeek V4 Flash 0731 (fp8) through OpenRouter;
- A1 on, unless the condition turns it off;
- a Docker sandbox capped at 2 CPUs and 4 GB, with no GPU;
- 2-hour runs.

## Test scores (mean over seeds)

| Condition | Spooky ↓ | Cactus ↑ | Nomad ↓ | Leaf ↓ |
|---|---|---|---|---|
| C1 | 0.3213 | 0.99963 | 0.06229 | 0.0331 |
| C2 (oracle) | 0.3213 | 0.99973 | 0.06159 | 0.0228 |
| C3 (top 3) | 0.3213 | 0.99967 | 0.06188 | 0.0294 |
| C4 | 0.3572 | 0.99969 | 0.06102 | 0.0791 |
| C5 | 0.3340 | 0.99970 | 0.06146 | 0.1700 |
| A1-off | 0.3375 | 0.99982 | 0.06102 | 7.8323 |
| A4-off | 0.3506 | 0.99950 | 0.05907 | 0.2751 |
| C6 | 0.3684 | 0.99953 | 0.06137 | 0.0261 |

**Medals:**
- Nomad: every run (12 silver, 1 bronze), and the C6 session (silver).
- Leaf: three runs. C4 seed 0 got silver (0.00145); C1 seed 2 and A1-off seed 0 got bronze.
- Spooky and cactus: none. Cactus's medals need a perfect AUC of 1.0.

**Seed noise is larger than the differences between conditions** on spooky, cactus and nomad:

| | Spooky | Cactus | Nomad |
|---|---|---|---|
| Range of C1 across seeds | 0.066 | 0.0008 | 0.0054 |
| Largest gap between two conditions' means | 0.036 | 0.0003 | 0.0032 |

On leaf, single bad runs dominate the means instead: C5 and A4-off each have one run at 0.364, and A1-off has one at 15.66.

## Interventions

| | Spooky | Cactus | Nomad | Leaf |
|---|---|---|---|---|
| C4 fired live | 0 of 3 runs | 0 of 3 | **1 of 3 (seed 0, twice)** | not recorded |
| C5 fired live | 1 of 3 (a false positive) | 0 of 3 | 1 of 3 (seed 0, twice, on crashed nodes) | not recorded |
| C4 rule replayed | fires once: A1-off seed 1, test 0.337 → 0.314 | never | (run folders not available) | (run folders not available) |
| C6 interventions | 12 (9 prunes) | 8 (all prunes) | 1 (a prune) | 0 |
| C6 prunes that C4 agrees with | 1 of 9 | 0 of 8 | 0 of 1 | |

## Main findings

### 1. A1 stops the agent from overfitting its own validation, but can't fix a tiny validation set

- **Without A1:**
  - on spooky seed 1, the agent fitted a stacker on its own validation split. Validation fell to 0.205 while test stayed at 0.337;
  - on nomad, A1-off had the largest gap between validation and test (+0.0047, about the size of a medal step);
  - on leaf, A1-off seed 1 scored 15.66, the worst run of the half plan (the package doesn't say why);
  - cactus didn't leak.
- **With A1,** the gap stayed under 0.015 on spooky, 0.0004 on cactus and 0.0015 on nomad.
- **Leaf is different, and not because of a leak.** With 178 validation rows for 99 species, most top nodes sit near 0 on validation. In the leaf C6 run, the pick had validation 0.0009, probe 0.179 and test 0.026. Validation can't separate models that are all nearly perfect on it.

### 2. The scripted monitors rarely acted

- **C4 fired live in one of nine runs where it's recorded:** nomad seed 0, twice. That's the only task where validation and probe moved apart steadily over several nodes with A1 on.
- **Replayed after the runs,** it also fires on spooky's leaking A1-off run, where it would have improved test by 0.023.
- **C5's live firings didn't help:**
  - on spooky, a false positive on a finding the probe confirmed;
  - on nomad, deleting findings that cited crashed nodes.
- **Leaf's package doesn't record** whether C4 or C5 acted.

### 3. People at the dashboard mostly pruned weak branches, or didn't act at all

- **Of 18 live prunes, one acted on a real gap between validation and probe:** spooky's n37, the same prune the C4 rule makes.
- **The rest followed cues the rule doesn't have:** branches far behind with little time left, the wrong model family, regressions. Nomad's one prune was a debug that made both scores worse.
- **On leaf, the participant made no interventions,** because it wasn't clear which changes justified one. On leaf the gap between validation and probe was large all the time, so it didn't single anything out.
- **None of the four sessions changed a submission.**

### 4. Final selection matters most where held-out splits are small

How much the oracle pick (C2) would have gained over C1's own pick:

| Spooky | Cactus | Nomad | Leaf |
|---|---|---|---|
| 0 on every seed | ≤ 0.0003 | 0.0001 to 0.0014 | **0.007 to 0.013** (about a third of C1's loss) |

- **On leaf, the oracle cuts C1's loss by about a third.** On the other tasks it gains under 2%.
- **In the leaf C6 run,** the best node (0.0119) would have been a bronze medal, while the pick scored 0.0261. That makes the final pick the intervention with the most to gain on leaf.

### 5. The probe's size decides which monitors can work

| Task | Probe rows | What the monitors could do with it |
|---|---|---|
| Spooky | 1,762 | trends are reliable; the C4 replay fires where the leak is |
| Nomad | ~216 | gaps pass C4's statistical check, and it fired live |
| Leaf | 89 | one row moves the probe a lot; the gap to validation is large all the time, and a person found no clear cue to act on |

### 6. Where the scores come from

- **Spooky:**
  - every run below 0.34 submitted naive Bayes combined with a linear model;
  - adding one ComplementNB to the C6 run improves its test score from 0.368 to 0.336 ([`spooky-drops.md`](spooky-drops.md));
  - the agent's own finding "prefer TF-IDF over NB" had steered that run away.
- **Cactus:** CNNs trained from scratch on CPU reach 0.999 within 26 nodes, the task's ceiling.
- **Nomad:** silver-level scores in almost every run.
- **Leaf:**
  - most runs score between 0.001 and 0.06;
  - a few score 0.2 to 0.36, and one 15.66;
  - so a few predictions decide the score.

## What the C6 participants wanted from the dashboard

- **Spooky:**
  - how likely a node is to be picked again;
  - what a redirect will actually do;
  - a way to cancel a queued action.
- **Cactus:**
  - progress before the first node finishes;
  - which node the search will extend next;
  - duplicates marked.
- **Nomad:**
  - trends of validation against probe along one branch;
  - the effect of an intervention;
  - whether a weak branch is likely to be explored again.
- **Leaf:** clearer guidance on when to intervene, especially when validation improves while the probe gets worse.

## Limitations

- **Few seeds and short runs.** 2 or 3 seeds of 2 hours on laptop CPUs. Seed noise, or on leaf single bad runs, is larger than the differences between conditions.
- **Nomad:**
  - two C1 runs made only 14 and 17 nodes;
  - several runs used other LLM providers;
  - the machine isn't recorded;
  - its run folders aren't here, so its rules can't be replayed.
- **Leaf:**
  - the machine and the C4 and C5 intervention logs aren't recorded;
  - there are no grid trajectories;
  - the cause of A1-off seed 1's 15.66 is unknown.
- **One model, offline:** DeepSeek V4 Flash, and no pretrained models in the sandbox.
- **Thresholds from pilots.** C4 and C5's thresholds came from a few pilots. C5's check on "hurts" findings treats a smaller harm on the probe as a failure.
- **C4 without A1 is a replay** on spooky.
- **The C6 sessions:**
  - one per task, by team members who aren't ML experts;
  - the AI assistant only explained the dashboard on spooky, but suggested every intervention on cactus;
  - the nomad prune was partly informed by discussion outside the dashboard;
  - the leaf session made no interventions.
- **All four tasks are public Kaggle competitions.** Their winning approaches are online and may be in the model's training data. The spooky and cactus participants didn't search online, to stay in the same position as the agent.

## Still to come

- **Nomad:** answers on the short C1 runs, the providers and the machine.
- **Leaf:** the C4 and C5 intervention logs, the machine, and the cause of A1-off seed 1.
