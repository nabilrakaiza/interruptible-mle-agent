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

- 4 hours wall clock per run
- 5 seeds for C1, C4, C5; 3 seeds for ablations
- Report bootstrapped 95% CIs; no ranking claims where intervals overlap

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
