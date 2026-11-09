# Leaf Classification – Additional Four-Hour Experiment Findings

## Experiment Overview

Eight additional Leaf Classification experiments were completed using a four-hour budget per run. These experiments covered Seeds 3 and 4 for C1, C4 and C5, and Seed 2 for A1-off and A4-off.

The earlier 13 experiments used a two-hour budget, so the two sets are reported separately.

All eight additional runs produced valid submissions.

## Results

| Condition | Runs | Mean Test Log Loss | Above Median | Medal Rate |
|---|---:|---:|---:|---:|
| C1 | 2 | 0.19301 | 50% | 0% |
| C2 (post hoc) | 2 | 0.00233 | 100% | 100% |
| C3 (post hoc, k=3) | 2 | 0.01811 | 100% | 50% |
| C4 | 2 | 0.06685 | 100% | 0% |
| C5 | 2 | 0.04934 | 100% | 0% |
| A1-off | 1 | 0.69775 | 0% | 0% |
| A4-off | 1 | 0.36429 | 0% | 0% |

Lower log loss is better. C2 and C3 are post-hoc selection analyses rather than separately trained conditions.

## Key Findings

### Autonomous Baseline (C1)

The two additional C1 runs showed considerable variation. Seed 3 achieved a test log loss of 0.34888, while Seed 4 achieved 0.03714.

### Divergence Pruning (C4)

Both additional C4 runs performed above the benchmark median, with test log losses of 0.07856 and 0.05514.

### Finding Correction (C5)

Both additional C5 runs also performed above the benchmark median, with test log losses of 0.07051 and 0.02816.

### Post-hoc Selection (C2 and C3)

C2 achieved a mean test log loss of 0.00233, substantially lower than the C1 mean of 0.19301.

This highlights the importance of final model selection. However, C2 uses test information after the run and cannot be used as a practical selection method.

### Ablation Results

A1-off Seed 2 achieved a test log loss of 0.69775, while A4-off Seed 2 achieved 0.36429. Both were valid submissions but performed below the benchmark median.

## Limitations

Only two additional seeds were evaluated for each main condition and one for each ablation. The four-hour experiments also used a different budget from the original two-hour runs, so comparisons should account for this difference.

## Conclusion

All eight additional experiments completed successfully and produced valid submissions. C4 and C5 performed above the benchmark median across their additional seeds, while C1 showed substantial variation.

The post-hoc results highlight the importance of model selection, but more comparable runs are needed before drawing strong conclusions about which intervention condition performs best.