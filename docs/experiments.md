# Experiment plan

## Tasks

Six MLE-bench Lite competitions, all CPU-feasible.

| Competition ID | Modality |
|---|---|
| `spooky-author-identification` | text |
| `detecting-insults-in-social-commentary` | text |
| `random-acts-of-pizza` | tabular |
| `nomad2018-predict-transparent-conductors` | tabular |
| `aerial-cactus-identification` | image (32x32) |
| `leaf-classification` | image, with precomputed tabular features |

## Budget and seeds

The proposal's plan:

- 4 hours wall clock per run
- 5 seeds for C1, C4, C5; 3 seeds for ablations
- Report bootstrapped 95% CIs; no ranking claims where intervals overlap

**Half plan first, for the slide submission (decided 25 Oct).** With about 3 days left in the run window, we run a smaller plan first so the slides have results from every condition: four tasks, one person per task, half the seeds, and one C6 session per person.

| | Proposal | Half plan |
|---|---|---|
| Tasks | 6 | 4: spooky, nomad, cactus, leaf |
| Wall clock per run | 4 h | 2 h |
| Seeds for C1, C4, C5 | 5 | 3 (0, 1, 2) |
| Seeds for A1-off, A4-off | 3 | 2 (0, 1) |
| C6 | a few sessions | one per person, on their own task |
| Runs per task | 21 | 13, plus 1 C6 session |
| Runs in total | 126 | 52, plus 4 C6 sessions |
| Machine-hours | ~500 | ~112 (~28 per person) |

**Who runs what.** Each person owns one task and runs all of its runs on their own machine:

| Task | Modality | Person |
|---|---|---|
| `spooky-author-identification` | text | Nabil |
| `nomad2018-predict-transparent-conductors` | tabular regression | to assign |
| `aerial-cactus-identification` | image | to assign |
| `leaf-classification` | image, with tabular features | to assign |

```bash
python scripts/launch_grid.py --only <task> --status   # this task's 13 runs: done, unfinished, to do
python scripts/launch_grid.py --only <task> --seed 0   # night 1: seed 0 of C1, C4, C5, A1-off, A4-off (5 runs, about 10 h)
python scripts/launch_grid.py --only <task> --seed 1   # night 2: seed 1 of all five (5 runs, about 10 h)
python scripts/launch_grid.py --only <task> --seed 2   # seed 2 of C1, C4, C5 (3 runs, about 6 h)
```

Go seed by seed, not condition by condition: after each night every condition has the same number of seeds, so a comparison is possible at any point. Without `--seed`, the launcher runs all of C1 before any C4. Rerunning a command resumes it, and a run cut off midway continues where it stopped. Each run takes about 2 hours and 2 minutes.

Each person's 13 runs take about 26 hours back to back, plus 2 hours for the C6 session, so a machine must run nearly non-stop until 28 Oct. Keep the laptop plugged in, awake (`caffeinate -i -s` on a Mac) and open.

**C6, individually.** Each person runs one C6 session on their own task, alone (`docs/c6-protocol.md`): the same person watches, intervenes and writes the notes. Fit it in between grid runs, at a time you can watch for the full 2 hours.

**Why these four tasks.** One per modality, and all four already have pilot runs (C4's thresholds were set from them). Insults and pizza are both binary AUC on short text and have no pilots, so they are the two dropped, following the rule in `docs/plan.md` (drop tasks before seeds).

**After the slides.** The full plan adds insults and pizza, C1/C4/C5 seeds 3 and 4, and ablation seed 2, by editing `configs/schedule.yaml`. The launcher skips finished runs, so every half-plan run counts towards the full plan. The budget stays 2 hours, so the two sets are comparable.

**The slides must state the half plan:** four tasks, 2-hour runs, and 3 or 2 seeds, so the intervals are wider than the proposal planned, and the C6 sessions had no separate observer.

## Conditions

| ID | Config | Notes |
|---|---|---|
| C1 | `c1_autonomous.yaml` | Baseline |
| C2 | none | Post hoc from C1 trees |
| C3 | none | Post hoc from C1 trees |
| C4 | `c4_divergence_prune.yaml` | Action intervention |
| C5 | `c5_finding_correction.yaml` | Belief intervention |
| C6 | `c6_live.yaml` | Few runs, think-aloud |
| A1-off | `ablation_a1_off.yaml` | A3 writes own split and metric |
| A4-off | `ablation_a4_off.yaml` | No findings |
| A2-off | `ablation_a2_off.yaml` | Optional |

## Metrics

**Outcome:** valid submission rate, above-median rate, any-medal rate.

**Process:** validation-test gap, gap over time, probe fidelity (probe vs test correlation), exploration diversity.

**Interaction cost:** interventions per run, timing, human time per intervention (C6), wall clock lost to abandoned nodes.

**Cost:** tokens per node and per run, API spend, wall clock, machine hours.

## Reliability checks

- **Leakage stress test:** planted leakage scripts plus clean controls; report A1 detection and false-positive rates.
- **Finding accuracy:** sample A4 findings, check support against cited nodes.
- **Prompt injection:** planted instruction in retrieval results; check propagation.

## Reproducibility

LLM outputs are nondeterministic even at temperature 0. Claims are distributional. Pin model versions, record seeds, log every call.

## Error taxonomy

Runtime error, timeout, invalid submission format, leakage, validation overfitting, unused data, stagnation.
