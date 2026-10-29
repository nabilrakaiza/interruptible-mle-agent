# Leaf Classification – Experimental Findings

## 1. Experiment Overview

We evaluated the interruptible MLE agent on the Leaf Classification task using five experimental conditions: C1 (Autonomous), C4 (Divergence Pruning), C5 (Finding Correction), A1-off and A4-off.

A total of 13 automated runs were completed, followed by one C6 live human-monitoring session. All 14 runs produced valid submissions.

The evaluation metric was multiclass log loss, where lower scores indicate better performance.

## 2. Automated Experiment Results

| Condition | Runs | Mean Test Log Loss | Above Median | Medal Rate |
|---|---:|---:|---:|---:|
| C1 | 3 | 0.03308 | 100% | 33% |
| C2 (post hoc) | 3 | 0.02280 | 100% | 33% |
| C3 (post hoc, k=3) | 3 | 0.02940 | 100% | 33% |
| C4 | 3 | 0.07912 | 67% | 33% |
| C5 | 3 | 0.16998 | 67% | 0% |
| A1-off | 2 | 7.83232 | 50% | 50% |
| A4-off | 2 | 0.27512 | 0% | 0% |

C2 and C3 were evaluated post hoc using existing runs and did not require separate training.

## 3. Key Findings

### Autonomous Performance (C1)

C1 produced consistently good results across all three seeds, with every submission performing above the benchmark median. One run earned a bronze medal.

### Divergence Pruning (C4)

C4 achieved the lowest individual test log loss of 0.00145 in Seed 0, earning a silver medal. However, performance varied across seeds, with Seed 1 recording a higher loss of 0.19893.

### Finding Correction (C5)

C5 produced valid submissions across all three seeds. Two runs performed above the benchmark median, but no medals were achieved.

### Ablation Results

A1-off showed substantial variation. Seed 0 achieved a bronze medal with a test loss of 0.00932, while Seed 1 had a much higher loss of 15.65532.

Both A4-off runs produced valid submissions but neither performed above the benchmark median.

These results suggest that performance is sensitive to the experimental condition and random seed. The small number of runs limits strong conclusions about differences between conditions.

## 4. C6 – Live Human Monitoring

The C6 experiment used Seed 100 and ran for approximately 120.9 minutes.

- Nodes explored: 49
- Working nodes: approximately 90%
- Human interventions: 0
- Final selected node: n33
- Validation log loss: 0.000885
- Probe log loss: 0.178746
- Test log loss: 0.026057
- Valid submission: Yes
- Above benchmark median: Yes
- Medal: None

During the session, I monitored the dashboard but did not intervene because I was unsure which changes justified pruning or redirecting the agent.

The replay analysis selected the same final node, n33, as the original run, with the same test log loss. This does not establish agreement on every potential pruning decision.

The trajectory also showed that improving validation loss did not always correspond to improving probe loss.

## 5. Limitations

The experiments used only two or three seeds per automated condition and one C6 live session. The Leaf Classification probe set was relatively small, making individual probe-score changes potentially noisy.

The C6 session involved no human interventions, so it cannot directly measure the effectiveness of human pruning or correction actions.

## 6. Conclusion

The agent completed all scheduled Leaf Classification experiments and generated valid submissions. C1 showed relatively consistent performance, while C4, C5 and the ablations displayed greater variation across seeds.

The C6 session highlighted the difficulty of deciding when human intervention is necessary. Clearer guidance on validation–probe divergence may help human monitors make more confident decisions in future sessions.