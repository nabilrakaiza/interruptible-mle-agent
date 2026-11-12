# Interaction cost

1 runs, 10 queued interventions.

## By condition

| condition | runs | queued_per_run | applied_per_run | dropped_per_run | first_applied_at | human_minutes_per_run | lost_wall_clock_s |
|---|---|---|---|---|---|---|---|
| C6 | 1 | 10.0 | 9.0 | 1.0 | 0.143 | 0.0 | 0.0 |

## By action and outcome

| condition | source_kind | action | outcome | n |
|---|---|---|---|---|
| C6 | human | prune | applied | 9 |
| C6 | human | prune | dropped | 1 |

## Why interventions were dropped

| reason | n |
|---|---|
| already pruned | 1 |

## Runs

| run | condition | task | seed | queued | applied | dropped | first_applied_at | human_minutes | lost_wall_clock_s | prune | redirect | override | inject | correct | rebudget |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C6_aerial-cactus-identification_seed102 | C6 | aerial-cactus-identification | 102 | 10 | 9 | 1 | 0.143 | 0.0 | 0.0 | 9 | 0 | 0 | 0 | 0 | 0 |
