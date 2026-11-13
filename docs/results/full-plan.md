# Findings of the full plan

Status on 9 Nov 2026. The full plan is 21 grid runs per task at 4 hours each: C1, C4 and C5 seeds 0 to 4, and A1-off and A4-off seeds 0 to 2. The half plan's findings are in [`findings.md`](findings.md).

**Full analysis of spooky, insults and pizza (Nabil):** [Full-plan results](https://claude.ai/artifact/1AHcCcSLLuLfqSGPkTFe5W#aee780ae-bfc4), with a cross-task summary, a tab per task (every run, charts, final models and a report draft), the reliability checks, tree shape and further analyses. A snapshot of it, with the charts, tables and scripts, is in [`analysis/`](analysis/README.md).

| Task | Modality | Grid runs | Where they ran | C6 |
|---|---|---|---|---|
| **spooky** | text | **21 of 21** at 4 h | Nabil's Mac (Docker) | 1 session (2 h) |
| **insults** | text | **21 of 21** at 4 h | Kaggle CPU (subprocess sandbox) | 1 session (2 h) |
| **pizza** | text + tabular | **21 of 21** at 4 h | Kaggle CPU (subprocess sandbox) | a 4 h run with Claude as the monitor ([`pizza/c6-4h.md`](pizza/c6-4h.md)) |
| leaf | image + tabular | 21 at 4 h (13 resumed from 2 h) | Medhini's machine | 1 session |
| cactus | image | 13 (half plan) at 2 h and again at 4 h ([`cactus/4h.md`](cactus/4h.md)) | Dziand's MacBook Pro (M2), Docker | 1 session (2 h), plus a 4 h run with Claude as the monitor ([`cactus/c6-4h.md`](cactus/c6-4h.md)) |
| nomad | tabular | 21 at 4 h (13 resumed from 2 h); 17 valid | Sahi's Windows ARM laptop (Snapdragon X), Docker on WSL2 | 1 session |

The run-by-run write-ups (merged here from `result-spooky`, `result-insults`, `result-pizza` and `result-leaf`):
- **spooky:** [`spooky/spooky.md`](spooky/spooky.md), with the full plan in [`spooky/sessions/night8.md`](spooky/sessions/night8.md) and the C6 session in [`spooky/c6.md`](spooky/c6.md);
- **insults:** [`insults/sessions/seed0.md`](insults/sessions/seed0.md) to [`insults/sessions/round5.md`](insults/sessions/round5.md), with the full plan in `insults/sessions/round5.md` and the C6 session in [`insults/c6.md`](insults/c6.md);
- **pizza:** [`pizza/sessions/seed0.md`](pizza/sessions/seed0.md) to [`pizza/sessions/round5.md`](pizza/sessions/round5.md), with the full plan in `pizza/sessions/round5.md`;
- **nomad** (merged from `result-nomad`): Sahi's full-plan package in [`nomad/full-4h/`](nomad/full-4h/README.md), 21 runs at 4 hours, 17 with a valid submission;
- **leaf** (merged from `result-leaf`): Medhini's full-plan package in [`leaf/full-4h/`](leaf/full-4h/findings.md), all 21 runs at 4 hours; the earlier 8-run four-hour set is in [`leaf/4h/`](leaf/4h/findings.md).

The rest of this page covers the three complete tasks.

## Setup

- **The same for all three:** DeepSeek V4 Flash 0731 (fp8) through OpenRouter, A1 on unless the condition turns it off, 4 hours and 2 CPUs per run.
- **Platforms differ by task, never within one:** spooky ran on a MacBook Pro M1 in Docker. Insults and pizza ran on Kaggle CPU with `--sandbox subprocess` (no isolation), because Kaggle has no Docker.
- **Routing:** StreamLake was excluded from 2 Nov, after it cut off 9% of its calls. Insults' and pizza's seed 0 and spooky's runs before 2 Nov used it; everything after didn't.
- **Spooky's seeds 0 to 2** started as 2-hour half-plan runs and were extended to 4 hours by resuming them.

| | Spooky | Insults | Pizza |
|---|---|---|---|
| Metric | log loss ↓ | AUC ↑ | AUC ↑ |
| Median / bronze / gold | 0.4188 / 0.2938 / – | 0.7784 / 0.7911 / 0.8332 | 0.5996 / 0.6921 / 0.9791 |
| Validation / probe rows | 1,762 probe | – | 576 / 288 |
| Cost of 21 runs | about $3.65 | about $8.70 | about $8.61 |

## Test scores (mean over seeds)

| Condition | Spooky ↓ | Insults ↑ | Pizza ↑ |
|---|---|---|---|
| C1 | 0.3290 | 0.9019 | **0.6978** |
| C2 (oracle, from C1) | 0.3284 | 0.9078 | 0.7037 |
| C3 (top 3, from C1) | 0.3288 | 0.9019 | 0.6983 |
| C4 | 0.3345 | 0.9054 | 0.6851 |
| C5 | **0.3133** | 0.9074 | 0.6847 |
| A1-off | 0.3592 | 0.9062 | 0.6851 |
| A4-off | 0.3424 | **0.9107** | 0.6818 |

| Medals | Spooky | Insults | Pizza |
|---|---|---|---|
| C1 | 0 of 5 | 5 gold of 5 | **4 bronze of 5** |
| C4 | 0 of 5 | 5 gold of 5 | 2 bronze of 5 |
| C5 | **1 bronze of 5** | 5 gold of 5 | 1 bronze of 5 |
| A1-off | 0 of 3 | 3 gold of 3 | 1 bronze of 3 |
| A4-off | 0 of 3 | 3 gold of 3 | 1 bronze of 3 |

**Every run on all three tasks made a valid submission above the median.**

## Main findings

### 1. No condition is clearly better than another

- **The best condition differs by task:** C5 on spooky, A4-off on insults, C1 on pizza.
- **On every task, one condition's own seeds vary more than the gaps between conditions.** Spooky's seeds range over 0.037 to 0.082 within a condition, against at most 0.046 between means. On pizza, C1 leads the next condition by 0.013 while A4-off alone ranges over 0.053. On insults, all means are within 0.009.
- **Medals don't separate them either:** insults is gold on all 21 runs, spooky has a single bronze, and pizza's bronze line sits in the middle of where its runs land.

Pizza's C1 (4 bronzes in 5, against 5 in 16 for the other conditions together) is the strongest hint of a difference, and it favours the condition without interventions.

### 2. A1 is what keeps validation honest

- **Spooky's A1-off seed 1 leaked:** the agent stacked models on its own validation split, and validation read 0.152 against test 0.408. A1-off is spooky's worst condition.
- **With A1 on, the pick's test stays within 0.015 of validation on all 18 spooky runs.**
- **On insults and pizza, A1-off didn't leak:** its picks' validation-to-test gaps (insults −0.001 to 0.017) are in the same range as the A1 runs'. A leak depends on what the agent happens to try.

### 3. The scripted interventions rarely had work, and didn't help when they did

| | Spooky | Insults | Pizza |
|---|---|---|---|
| C4, live (5 runs) | never fired | never fired | 3 prunes in 2 runs, pick never changed |
| C5, live (5 runs) | 2 corrections, pick never changed | never fired | 11 corrections |
| C4 rule, replayed on other runs | fires on 3: helps 1 (the A1-off leak) | never fires | fires on 8: helps 2, no change 3, worse 3 |

- **Where validation and probe move together (spooky with A1, insults), the rules see nothing.** C4 and C5 runs are then C1's agent on other random paths.
- **On pizza, with a 288-row probe, they fire on noise.** For C5's seeds 2 to 4, every deleted finding that made a claim (5 of 5) was right according to test. In 4 of the 5, test sided with validation against the probe.
- **The one clear win is the replayed C4 rule on spooky's leaking A1-off run,** where it would have improved the pick from 0.408 to 0.314. A1 already prevents that leak.

### 4. Final selection costs little, except on pizza

- **The pick is a median 0.000 below the run's best node on spooky, 0.003 on insults and 0.009 on pizza.**
- **The top-3 hedge (C3) barely helps:** at most 0.0005 on average over C1's runs on any task.
- **Pizza's validation is optimistic:** the pick's test is below its validation on 20 of 21 runs, by 0.026 on average. With 576 rows, the best validation score is partly luck, and near-ties on validation (within 0.001 to 0.003) separated nodes up to 0.017 apart on test. The largest pick loss was 0.035 (C4 seed 2).

### 5. On spooky, the model family matters more than the condition

The 9 best spooky runs all submitted naive Bayes combined with a linear model, and the three weakest runs with A1 didn't use that combination. The half plan's stricter rule ("every run below 0.34 combined them", [`spooky/drops.md`](spooky/drops.md)) doesn't hold at 4 hours: 4 of the 14 runs under 0.34 didn't. Which family the agent lands on early still separates spooky's runs more than any condition does.

### 6. Speed and cut-off calls changed between seeds

- **Excluding StreamLake made runs about twice as fast** (insults: 51 to 86 nodes on seed 0, 35 to 200 later), so seed 0 compares the conditions at less search time than later seeds. Within a seed, all conditions ran under the same routing.
- **Calls cut off at the 64k-token cap:** 3.3% on insults, 5.2% on pizza, and 17 of 1,626 calls on spooky. The rate varies from day to day with the same routing (0.3% to 12% a round on pizza).

## C6 sessions

- **Spooky:** one 2-hour session (seed 100), test 0.368. Compared with C1 at the 2-hour mark of its five runs (0.295 to 0.390, mean 0.344, read from their checkpoints), it's within C1's range. Of its 12 interventions, 8 of the 9 prunes followed a budget cue the C4 rule doesn't have ([`spooky/c6.md`](spooky/c6.md)).
- **Insults:** one 2-hour session (seed 100, 8 Nov, on the Mac in Docker), test 0.9087 (gold), within C1's range at the 2-hour mark (0.901 to 0.909, mean 0.9055). 8 interventions; the participant could choose which node the agent worked on but not what it changed ([`insults/c6.md`](insults/c6.md)).
- **Pizza:** no session with a person. A 4-hour run (seed 100, 12 Nov, Dziand's Mac in Docker) used Claude as the monitor: 79 prunes, mostly of children below their parent on validation, which on pizza's 576 validation rows is noise. Test 0.6671, below every C1 run; the best nodes on test were among those pruned ([`pizza/c6-4h.md`](pizza/c6-4h.md)).

## Limitations

- **Five seeds for C1, C4 and C5, three for the ablations.** Intervals overlap everywhere; no ranking is claimed.
- **Insults and pizza ran without sandbox isolation** (Kaggle has no Docker). Their scripts had network access.
- **Seed 0 used StreamLake** on all three tasks, so it ran slower than later seeds.
- **Spooky's seeds 0 to 2 were resumed** from 2 to 4 hours rather than run in one go. A resumed run continues from its last checkpoint with the same tree, so this shouldn't change its course, but it isn't identical to a single run.
