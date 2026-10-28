# Findings of the half plan so far

Two of the four tasks are complete: **spooky** (text, Nabil) and **cactus** (image, Dziand). Each has 13 grid runs and a C6 session. Nomad and leaf will be added when their results are in.

Each task has its own summary, and the per-seed and C6 write-ups are linked from it:

- [`spooky.md`](spooky.md), with [`spooky-c6.md`](spooky-c6.md) and [`spooky-drops.md`](spooky-drops.md)
- [`cactus.md`](cactus.md), with [`cactus-c6.md`](cactus-c6.md)

## Setup

| | Spooky | Cactus |
|---|---|---|
| Task | predict a sentence's author (3 classes) | detect cacti in 32×32 aerial images |
| Metric | log loss, **lower** is better | ROC AUC, **higher** is better |
| MLE-bench median / bronze | 0.4188 / 0.2938 | 0.9991 / 1.0 (every medal needs a perfect score) |
| Machine | 13-inch MacBook Pro 2020, Apple M1, 8 GB | 13-inch MacBook Pro 2022, Apple M2, 8 GB |
| Docker VM (Colima) | 2 CPUs, 4 GB | 2 CPUs, 5 GB |
| Grid runs | 13, all valid and above the median | 13, all valid and above the median |
| C6 | 1 watched session (seed 100) | 1 watched session (seed 101), plus 1 unwatched run (seed 100) |
| Cost | $1.00 for the grid + $0.13 for C6 | $1.12 for the grid + $0.25 for the two C6 runs |

Both tasks used the same setup:
- DeepSeek V4 Flash 0731 (fp8) through OpenRouter;
- A1 on, unless the condition turns it off;
- a Docker sandbox capped at 2 CPUs and 4 GB, with no GPU;
- 2-hour runs, one at a time;
- seeds 0 to 2 for C1, C4 and C5, and seeds 0 and 1 for A1-off and A4-off.

## Test scores

**Spooky** (log loss, lower is better)

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.3606 | 0.3087 | 0.2946 | 0.3213 |
| C2 (oracle, from C1) | 0.3606 | 0.3087 | 0.2946 | 0.3213 |
| C3 (top 3, from C1) | 0.3606 | 0.3087 | 0.2946 | 0.3213 |
| C4 | 0.3808 | 0.3339 | 0.3568 | 0.3572 |
| C5 | 0.3632 | 0.2973 | 0.3414 | 0.3340 |
| A1-off | 0.3377 | 0.3374 | n/a | 0.3375 |
| A4-off | 0.3361 | 0.3651 | n/a | 0.3506 |
| C6 | 0.3684 (seed 100) | | | |

**Cactus** (AUC, higher is better)

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.99977 | 0.99994 | 0.99917 | 0.99963 |
| C2 (oracle, from C1) | 0.99982 | 0.99994 | 0.99942 | 0.99973 |
| C3 (top 3, from C1) | 0.99977 | 0.99994 | 0.99929 | 0.99967 |
| C4 | 0.99936 | 0.99992 | 0.99979 | 0.99969 |
| C5 | 0.99999 | 0.99927 | 0.99984 | 0.99970 |
| A1-off | 0.99972 | 0.99993 | n/a | 0.99982 |
| A4-off | 0.99961 | 0.99940 | n/a | 0.99950 |
| C6 | 0.99953 (seed 101) | | | |

**On neither task is any condition clearly better than another.** One condition's seeds differ by more than the gap between any two conditions' means:

| | Spooky | Cactus |
|---|---|---|
| Range of C1 across seeds | 0.066 | 0.0008 |
| Largest gap between two conditions' means | 0.036 | 0.0003 |

No medals were won. On spooky, the closest was C1 seed 2, 0.0008 short of bronze. On cactus, every medal needs an AUC of 1.0, which no node reached.

## Interventions

| | Spooky | Cactus |
|---|---|---|
| C4 (prune) fired in a live run | 0 of 3 runs | 0 of 3 runs |
| C5 (finding correction) fired in a live run | 1 of 3 runs (seed 2), no effect | 0 of 3 runs |
| C4 rule replayed over all 13 runs | fires once: A1-off seed 1, test 0.337 → 0.314 | never |
| C5 rule replayed over all 13 runs | only on A1-off seed 1: 2 findings about the leaking stacker, no effect on the pick | twice, on findings citing crashed nodes, no effect |
| C6: interventions by the person | 12 (9 prunes, 2 redirects, 1 correction) | 8 (all prunes) |
| C6: prunes the C4 rule agrees with | 1 of 9 (n37, a real divergence) | 0 of 8 (the rule never fires) |
| C6: effect on the submission | none measurable | none measurable |
| C6: assistant's role | explained the dashboard; no intervention ideas | explained the dashboard **and suggested every intervention** |

## Main findings

### 1. A1 matters where the agent can fool its own validation

Without A1, the agent writes its own validation split and metric.
- **On spooky seed 1** it stacked its models with a logistic regression fitted on its own validation split, then scored the stack on that same split. Validation fell to 0.205, test stayed at 0.337, and the submitted node ranked 27th of 55 on test. That's a 0.132 gap between validation and test.
- **On cactus,** A1-off's gaps stayed within 0.0002. With every model near 0.999 AUC, fitting to its own split gains nothing.
- **With A1 on,** the submitted node's validation stayed within 0.015 of test on spooky, and within 0.0004 on cactus.

### 2. The scripted monitors almost never had work to do

- **With A1 on, validation and probe moved together** in every run on both tasks.
- **C4 never fired in a live run** (0 of 6 runs).
- **C5 fired once,** on spooky seed 2, and that was a false positive. It deleted a finding that the probe actually confirmed, because the probe showed a smaller harm than validation did. It changed nothing.
- **Replayed after the runs,** the C4 rule fires in exactly one of 26 runs: spooky A1-off seed 1, the run with the leak. There it would have improved test by 0.023.

So an action intervention helps exactly where the agent's own signal breaks, and stays silent otherwise. With A1 on, the signal never broke in these runs.

### 3. People at the dashboard mostly pruned waste

- **The two C6 sessions made 17 prunes in total.** Only one acted on a divergence between validation and probe: spooky's n37, the same prune the C4 rule would make.
- **The other 16 followed cues the rule doesn't have:**
  - a branch far behind with little time left;
  - a model family going nowhere (cactus's non-CNN drafts);
  - a regression against its siblings.
- **None of them changed the submission** on either task.
- **Both participants kept the agent's validation-best pick** over a probe-best or other alternative, and both choices were right or tied on test:
  - spooky: n49 (0.3684) against n30 (0.3723);
  - cactus: n13 against n8, 0.00003 apart.

### 4. What the interventions can and can't do

- **A redirect chooses which node gets improved, not what the agent changes.** Both of spooky's redirects produced nothing. The agent repeated n4's result, and undid n30's change because its findings said it hadn't helped on validation.
- **A prune chooses where the search doesn't go, not where it goes.** After cactus's last prune, the search spent its final 25 minutes rebuilding two earlier nodes from another weak one.
- **Prunes act late.** They apply between nodes, so a branch keeps growing while a prune waits. On cactus, two pruned nodes' children had already run.
- **Some cues mislead.** On cactus, the first instinct was to prune the best node because its two children scored lower. On spooky, the probe's ranking of two drafts (n0 against n1) turned out to be noise.

### 5. Final selection rarely matters with A1 on

- **C2 (oracle) and C3 (top 3) matched C1** on all three spooky seeds. On cactus they beat it by at most 0.00025.
- **Across all runs with A1, the oracle would have gained:**
  - on spooky, 0.004 at most (C5 seed 1, where it would have reached bronze);
  - on cactus, 0.0003 at most.
- **Without A1, it mattered:** on spooky seed 1, the oracle would have gained 0.023.

### 6. Where the scores come from

- **Spooky:** every run below 0.34 submitted naive Bayes combined with a linear model. Every run that didn't stayed at 0.34 or above.
  - **C6's agent never built that combination.** An early finding of its own said "prefer TF-IDF over NB". That was true for the two drafts it compared, but wrong for what mattered later.
  - **Adding one ComplementNB** to C6's submitted script improves its test score from 0.368 to 0.336 ([`spooky-drops.md`](spooky-drops.md)).
  - **What this means:** a finding can be true and still steer the search the wrong way. Spotting that takes ML expertise, which neither the scripted rules nor our non-expert participants had.
- **Cactus:** every run reached 0.999 within its first 26 nodes, using CNNs trained from scratch on CPU. After that the search only moved the fourth decimal.

### 7. Cactus is the control task

On cactus:
- no scripted monitor intervened;
- A1-off did not leak;
- the person at the dashboard found only waste to prune;
- every condition ended within 0.0008 of a perfect score.

Next to spooky's A1-off seed 1, it shows that A1 and the interventions matter where the agent's own signal can mislead it, not everywhere.

## What the C6 participants wanted from the dashboard

- **Spooky:**
  - how likely a node is to be picked again;
  - what a redirect will actually do;
  - a way to cancel a queued action.
- **Cactus:**
  - progress before the first node finishes (13 minutes of an empty tree looked like a stuck run);
  - which node the search will extend next;
  - duplicates marked (n11 = n7, n29 = n8).

## Limitations

- **Few seeds and short runs.** 3 seeds for C1, C4 and C5 and 2 for the ablations; 2-hour runs on 2 CPUs, on two different 8 GB laptops. Seed noise is larger than every difference between conditions.
- **One model,** DeepSeek V4 Flash, and no pretrained models, since the sandbox is offline.
- **Thresholds from pilots.** C4 and C5's thresholds were set from a handful of pilot runs. C5's check on "hurts" findings treats a smaller harm on the probe as a failure.
- **C4 without A1 is a replay.** Its gain on spooky's A1-off run isn't a measured condition.
- **The two C6 sessions aren't comparable with each other.**
  - On spooky, the assistant only explained the dashboard.
  - On cactus, it suggested every intervention.
  - Both participants are team members, not ML experts, who knew the agent and had seen their task's other runs.
  - Neither session had a separate observer.
- **Cactus is at the ceiling,** so it can't separate conditions by score.
- **Both tasks are public Kaggle competitions,** so their winning approaches are online and may be in the model's training data. Neither participant searched online, to stay in the same position as the offline agent. On tasks whose solutions aren't public, both the agent and the monitor could be allowed to search.

## Still to come

- **Nomad** (Sahi): 13 runs are on `result-nomad`, in a different layout (`results/nomad2018/`). Still to check: two C1 runs with only 14 and 17 nodes, a mix of LLM providers, the machine used, and the C6 session.
- **Leaf:** no results on any branch yet.
