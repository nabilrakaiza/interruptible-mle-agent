# Interaction cost

1 runs, 94 queued interventions.

## By condition

| condition | runs | queued_per_run | applied_per_run | dropped_per_run | first_applied_at | human_minutes_per_run | lost_wall_clock_s |
|---|---|---|---|---|---|---|---|
| C6 | 1 | 94.0 | 79.0 | 15.0 | 0.079 | 0.0 | 0.0 |

## By action and outcome

| condition | source_kind | action | outcome | n |
|---|---|---|---|---|
| C6 | human | prune | applied | 79 |
| C6 | human | prune | dropped | 15 |

## Why interventions were dropped

| reason | n |
|---|---|
| already pruned | 15 |

## Runs

| run | condition | task | seed | queued | applied | dropped | first_applied_at | human_minutes | lost_wall_clock_s | prune | redirect | override | inject | correct | rebudget |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C6_random-acts-of-pizza_seed100 | C6 | random-acts-of-pizza | 100 | 94 | 79 | 15 | 0.079 | 0.0 | 0.0 | 79 | 0 | 0 | 0 | 0 | 0 |
