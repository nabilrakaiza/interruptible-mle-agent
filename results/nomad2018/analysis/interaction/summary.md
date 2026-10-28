# Interaction cost

13 runs, 4 queued interventions.

## By condition

| condition | runs | queued_per_run | applied_per_run | dropped_per_run | first_applied_at | human_minutes_per_run | lost_wall_clock_s |
|---|---|---|---|---|---|---|---|
| A1-off | 2 | 0.0 | 0.0 | 0.0 |  | 0.0 | 0.0 |
| A4-off | 2 | 0.0 | 0.0 | 0.0 |  | 0.0 | 0.0 |
| C1 | 3 | 0.0 | 0.0 | 0.0 |  | 0.0 | 0.0 |
| C4 | 3 | 0.667 | 0.667 | 0.0 | 0.537 | 0.0 | 0.0 |
| C5 | 3 | 0.667 | 0.667 | 0.0 | 0.268 | 0.0 | 0.0 |

## By action and outcome

| condition | source_kind | action | outcome | n |
|---|---|---|---|---|
| C4 | policy | prune | applied | 2 |
| C5 | policy | correct | applied | 2 |

## Why interventions were dropped

(none)

## Runs

| run | condition | task | seed | queued | applied | dropped | first_applied_at | human_minutes | lost_wall_clock_s | prune | redirect | override | inject | correct | rebudget |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1-off_nomad2018-predict-transparent-conductors_seed0 | A1-off | nomad2018-predict-transparent-conductors | 0 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| A1-off_nomad2018-predict-transparent-conductors_seed1 | A1-off | nomad2018-predict-transparent-conductors | 1 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| A4-off_nomad2018-predict-transparent-conductors_seed0 | A4-off | nomad2018-predict-transparent-conductors | 0 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| A4-off_nomad2018-predict-transparent-conductors_seed1 | A4-off | nomad2018-predict-transparent-conductors | 1 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C1_nomad2018-predict-transparent-conductors_seed0 | C1 | nomad2018-predict-transparent-conductors | 0 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C1_nomad2018-predict-transparent-conductors_seed1 | C1 | nomad2018-predict-transparent-conductors | 1 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C1_nomad2018-predict-transparent-conductors_seed2 | C1 | nomad2018-predict-transparent-conductors | 2 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C4_nomad2018-predict-transparent-conductors_seed0 | C4 | nomad2018-predict-transparent-conductors | 0 | 2 | 2 | 0 | 0.537 | 0.0 | 0.0 | 2 | 0 | 0 | 0 | 0 | 0 |
| C4_nomad2018-predict-transparent-conductors_seed1 | C4 | nomad2018-predict-transparent-conductors | 1 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C4_nomad2018-predict-transparent-conductors_seed2 | C4 | nomad2018-predict-transparent-conductors | 2 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C5_nomad2018-predict-transparent-conductors_seed0 | C5 | nomad2018-predict-transparent-conductors | 0 | 2 | 2 | 0 | 0.268 | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 2 | 0 |
| C5_nomad2018-predict-transparent-conductors_seed1 | C5 | nomad2018-predict-transparent-conductors | 1 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C5_nomad2018-predict-transparent-conductors_seed2 | C5 | nomad2018-predict-transparent-conductors | 2 | 0 | 0 | 0 |  | 0.0 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |
