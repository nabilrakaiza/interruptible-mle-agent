# Findings of the half plan so far

All four tasks now have results, but not all of them are complete:

| Task | Modality | Owner | Grid runs | C6 |
|---|---|---|---|---|
| **spooky** | text | Nabil | 13 of 13 | 1 session |
| **cactus** | image | Dziand | 13 of 13 | 1 session, plus 1 unwatched run |
| **nomad** | tabular | Sahi | 13 of 13 | none yet |
| **leaf** | image + tabular | Medhini | **2 of 13** (C1 and C4, seed 0), run by Nabil | none yet |

Each task has its own write-up:
- [`spooky.md`](spooky.md), with [`spooky-c6.md`](spooky-c6.md) and [`spooky-drops.md`](spooky-drops.md)
- [`cactus.md`](cactus.md), with [`cactus-c6.md`](cactus-c6.md)
- [`nomad.md`](nomad.md), a summary of Sahi's package in [`../../results/nomad2018/`](../../results/nomad2018/README.md)
- [`leaf-seed0.md`](leaf-seed0.md)

## Setup

| | Spooky | Cactus | Nomad | Leaf |
|---|---|---|---|---|
| Metric | log loss ↓ | ROC AUC ↑ | RMSLE ↓ | log loss ↓ |
| Median / bronze | 0.4188 / 0.2938 | 0.9991 / 1.0 | 0.0699 / 0.0658 | 0.1083 / 0.0153 |
| Probe split | 1,762 rows | | ~216 rows | 89 rows (99 classes) |
| Machine | MacBook Pro M1, 8 GB | MacBook Pro M2, 8 GB | not recorded | MacBook Pro M1, 8 GB |

All four used the same setup:
- DeepSeek V4 Flash 0731 (fp8) through OpenRouter;
- A1 on, unless the condition turns it off;
- a Docker sandbox capped at 2 CPUs and 4 GB, with no GPU;
- 2-hour runs, one at a time.

## Test scores (mean over seeds)

| Condition | Spooky ↓ | Cactus ↑ | Nomad ↓ | Leaf ↓ (seed 0) |
|---|---|---|---|---|
| C1 | 0.3213 | 0.99963 | 0.06229 | 0.1018 |
| C2 (oracle) | 0.3213 | 0.99973 | 0.06159 | 0.0357 |
| C3 (top 3) | 0.3213 | 0.99967 | 0.06188 | 0.0956 |
| C4 | 0.3572 | 0.99969 | 0.06102 | 0.3489 |
| C5 | 0.3340 | 0.99970 | 0.06146 | |
| A1-off | 0.3375 | 0.99982 | 0.06102 | |
| A4-off | 0.3506 | 0.99950 | 0.05907 | |
| C6 | 0.3684 | 0.99953 | | |

**Medals:**
- Nomad: every run (12 silver, 1 bronze).
- Spooky and cactus: none. Cactus's medals need a perfect AUC of 1.0.
- Leaf: none, and C4 fell below the median.

**On every task, seed noise is larger than the differences between conditions:**

| | Spooky | Cactus | Nomad |
|---|---|---|---|
| Range of C1 across seeds | 0.066 | 0.0008 | 0.0054 |
| Largest gap between two conditions' means | 0.036 | 0.0003 | 0.0032 |

## Interventions

| | Spooky | Cactus | Nomad | Leaf |
|---|---|---|---|---|
| C4 fired live | 0 of 3 runs | 0 of 3 | **1 of 3 (seed 0, twice)** | 0 of 1 |
| C5 fired live | 1 of 3 (a false positive) | 0 of 3 | 1 of 3 (seed 0, twice, on crashed nodes) | not run |
| C4 rule replayed | fires once: A1-off seed 1, test 0.337 → 0.314 | never | (run folders not available) | never (64% of resamples at n43; needs 95%) |
| C5 rule replayed | A1-off seed 1 only, no effect | twice, no effect | (not available) | 9 findings over 2 runs, on probe noise |
| C6 interventions | 12 (9 prunes) | 8 (all prunes) | | |
| C6 prunes that C4 agrees with | 1 of 9 | 0 of 8 | | |

## Main findings

### 1. A1 stops the agent gaming its own score, but not small-sample luck

- **Without A1:**
  - on spooky seed 1, the agent fitted a stacker on its own validation split. Validation fell to 0.205 while test stayed at 0.337;
  - on nomad, A1-off had the largest gap between validation and test (+0.0047, about the size of a medal step);
  - cactus didn't leak.
- **With A1,** the gap stayed under 0.015 on spooky, 0.0004 on cactus and 0.0015 on nomad.
- **Leaf is the exception, and not a leak.** With A1 on, C4's pick scored 0.0000 on validation and 0.349 on test:
  - every top node gets about 99% of rows right;
  - validation (178 rows for 99 species) happened to contain no hard row;
  - test had one hard row, which the chosen model got wrong with near-certainty.
  - Choosing by validation rewarded the most overconfident model.

### 2. The scripted monitors rarely acted, and acted right when they did

- **C4 fired live in one of ten runs:** nomad seed 0, twice. That's the only task where validation and probe diverged steadily over several nodes with A1 on.
- **Replayed after the runs,** it also fires on spooky's leaking A1-off run, where it would have improved test by 0.023.
- **It stayed silent on leaf's one-row divergence** by design. The probe loss there rests on one row and holds in only 64% of resamples.
- **C5's live firings didn't help:**
  - on spooky, a false positive on a confirmed finding;
  - on nomad, deleting findings that cited crashed nodes.
- **Replayed on leaf, C5 would mostly act on probe noise:** 89 rows for 99 species.

### 3. People at the dashboard mostly pruned waste

Spooky and cactus only; no C6 on nomad or leaf yet.
- **Of 17 live prunes, one acted on a real divergence:** spooky's n37, the same prune the C4 rule makes.
- **The rest followed cues the rule doesn't have:** branches far behind with little time left, the wrong model family, regressions.
- **None changed a submission.**

### 4. Final selection matters most where held-out splits are small

How much the oracle pick would have gained over the agent's own:

| Spooky | Cactus | Nomad | Leaf |
|---|---|---|---|
| ≤ 0.004 | ≤ 0.0003 | 0.0001 to 0.0014 | **0.066 (C1) and 0.296 (C4)** |

On leaf, the best node on test was several times better than the submitted one. That makes the final pick the intervention with the most to gain there.

### 5. The probe's size decides which monitors can work

| Task | Probe rows | What the monitors could do with it |
|---|---|---|
| Spooky | 1,762 | trends are reliable; the C4 replay fires where the leak is |
| Nomad | ~216 | divergences pass C4's statistical check, and it fired live |
| Leaf | 89 | one row moves the probe a lot; C4's check rightly refuses, and C5 reacts to noise |

A person can still see a leaf-style divergence on the dashboard. The question is whether they act on it.

### 6. Where the scores come from

- **Spooky:**
  - every run below 0.34 submitted naive Bayes combined with a linear model;
  - adding one ComplementNB to the C6 run improves its test score from 0.368 to 0.336 ([`spooky-drops.md`](spooky-drops.md));
  - the agent's own finding "prefer TF-IDF over NB" had steered that run away.
- **Cactus:** CNNs trained from scratch on CPU reach 0.999 within 26 nodes, the task's ceiling.
- **Nomad:** silver-level scores in almost every run.
- **Leaf:** about 99% accuracy everywhere. The score is decided by calibration on the one or two rows a model misses.

## What the C6 participants wanted from the dashboard

- **Spooky:**
  - how likely a node is to be picked again;
  - what a redirect will actually do;
  - a way to cancel a queued action.
- **Cactus:**
  - progress before the first node finishes;
  - which node the search will extend next;
  - duplicates marked.

## Limitations

- **Few seeds and short runs.** 2 or 3 seeds of 2 hours on laptop CPUs. Seed noise is larger than every difference between conditions.
- **Leaf is two runs,** C1 and C4 of seed 0, run by Nabil. Medhini's own runs are still to come.
- **Nomad:**
  - two C1 runs made only 14 and 17 nodes;
  - several runs used other LLM providers;
  - the machine isn't recorded;
  - its run folders aren't here, so its rules can't be replayed.
- **One model, offline:** DeepSeek V4 Flash, and no pretrained models in the sandbox.
- **Thresholds from pilots.** C4 and C5's thresholds came from a few pilots. C5's check on "hurts" findings treats a smaller harm on the probe as a failure.
- **C4 without A1 is a replay** on spooky.
- **The C6 sessions:**
  - only two, on spooky and cactus, by team members who aren't ML experts;
  - the assistant only explained the dashboard on spooky, but suggested every intervention on cactus.
- **All four tasks are public Kaggle competitions.** Their winning approaches are online and may be in the model's training data. Neither participant searched online, to stay in the same position as the agent.

## Still to come

- **Leaf:** Medhini's runs, and a C6 session.
- **Nomad:** a C6 session, and answers on the short C1 runs, the providers and the machine.
