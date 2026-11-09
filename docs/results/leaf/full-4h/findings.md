# Leaf Classification – Full Four-Hour Experiment Findings

## 1. Experiment Overview

The full Leaf Classification experiment plan included 21 automated runs, each with a four-hour total budget.

- C1, C4 and C5: Five seeds each (0–4).
- A1-off and A4-off: Three seeds each (0–2).
- C2 and C3: Post-hoc analyses of the five C1 runs.

The original 13 runs were extended from two to four hours using saved checkpoints. The remaining eight runs were conducted separately with four-hour budgets.

All 21 runs produced valid submissions.

The evaluation metric was multiclass log loss, where lower scores indicate better performance.

## 2. Full Experiment Results

| Condition | Runs | Mean Test Log Loss | Above Median | Medal Rate |
|---|---:|---:|---:|---:|
| C1 | 5 | 0.08486 | 80% | 40% |
| C2 (post hoc) | 5 | 0.00750 | 100% | 80% |
| C3 (post hoc, k=3) | 5 | 0.01490 | 100% | 60% |
| C4 | 5 | 0.10336 | 80% | 20% |
| C5 | 5 | 0.16599 | 60% | 0% |
| A1-off | 3 | 5.45413 | 33% | 33% |
| A4-off | 3 | 0.24279 | 33% | 33% |

## 3. Key Findings

### Autonomous Baseline (C1)

C1 achieved a mean test log loss of 0.08486. Four out of five runs performed above the benchmark median, and two received medals.

### Divergence Pruning (C4)

C4 achieved a mean test log loss of 0.10336. Four out of five runs performed above the benchmark median, with one silver medal.

C4 did not consistently outperform the autonomous baseline in this experiment.

### Finding Correction (C5)

C5 achieved a mean test log loss of 0.16599. Three out of five runs performed above the benchmark median, and none received medals.

The results did not show a consistent improvement over C1.

### Post-hoc Selection (C2 and C3)

C2 achieved a mean test log loss of 0.00750, while C3 achieved 0.01490.

Both performed better than C1 in the post-hoc analysis, highlighting the importance of final model selection.

However, C2 uses test scores after the run and is not a deployable model-selection method.

### Ablation Results

A1-off showed substantial variation across seeds, including one run with a test log loss of 15.65532.

A4-off also varied considerably, including one run with a reported test log loss of 0.0 and a gold medal.

The zero-loss result is the official grader's reported score, but it should not be interpreted as proof of perfect generalization without further investigation.

## 4. Limitations

Although the experiments used four-hour budgets, there were only five seeds per main condition and three per ablation. The small sample sizes limit statistical conclusions about which condition performs best.

The Leaf Classification probe set was also relatively small, so individual predictions could strongly affect the observed scores.

## 5. Conclusion

All 21 automated Leaf Classification experiments completed successfully and produced valid submissions.

The autonomous baseline achieved a lower mean test log loss than C4 and C5, while post-hoc selection showed substantial potential improvements from choosing a better final model.

Overall, the results highlight the importance of reliable evaluation, careful model selection and accounting for variability across random seeds.