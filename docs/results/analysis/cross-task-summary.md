# Cross-task summary

> Exported 9 Nov 2026 from Nabil's analysis doc, [Full-plan results](https://claude.ai/artifact/1AHcCcSLLuLfqSGPkTFe5W), tab “Cross-task summary”. Charts are images of the doc's live charts. Paths under `runs/` are on Nabil's Mac; the data and scripts used are copied next to this file.

Across spooky, insults and pizza (63 runs, 4 hours each), the agent is reliable, A1 is what keeps its validation honest, and neither scripted intervention improved the outcome. This tab lists what holds on all three tasks and what differs; the task tabs hold the evidence.

## What holds on all three tasks

1. **Reliable:** 63 of 63 runs made a valid submission above the median; insults is gold on 21 of 21, pizza bronze on 9, spooky bronze on 1. The 63 runs cost about $21.
2. **No condition is better:** a Friedman test across tasks finds no difference between C1, C4 and C5 (p = 0.55) or among all five conditions (p = 0.69). The best condition differs by task: C5 on spooky, A4-off on insults, C1 on pizza.
3. **A1 keeps validation honest:** without A1, the pick's validation is more optimistic on every task (median gap 0.088, 0.015 and 0.045 against 0.006, 0.001 and 0.021 with A1), and one spooky run leaked (validation 0.152, test 0.408). With A1 no run leaked; its screen caught 4 of 4 planted leaks and stopped 3 real scripts.
4. **The interventions had little to do and did not help:** C4 pruned live only on pizza (3 prunes, no pick changed); C5's 13 corrections changed no pick, and on pizza most deleted findings were right. Replayed, the C4 rule helped clearly only on the leaking spooky run, which A1 already prevents.
5. **The model family matters more than the condition:** naive Bayes combined with a linear model separates the best runs on spooky and insults; pizza's best runs are tree ensembles; refitting more complex models on insults' best features did not help.
6. **Picking by validation is the best simple rule:** picking by the probe, or by both, is never better on average.
7. **The agent's findings are unreliable:** about 60% are supported by the scores they cite, and only 22% to 50% hold on the probe.
8. **Most improvement attempts fail:** 50% to 69% of working improve nodes do not beat their parent.

## What differs, and why

|  | Spooky | Insults | Pizza |
| --- | --- | --- | --- |
| Validation / probe rows | 3,524 / 1,762 | 789 / 395 | 576 / 288 |
| Probe ranks nodes like test (rank correlation) | 0.97 | 0.59 | 0.28 |
| Pick's loss to the run's best node (median) | 0.000 | 0.003 | 0.009 |
| Interventions that fired (live) | 2 corrections | none | 3 prunes, 11 corrections |
| Tree shape | deep | wide | wide |
| Pick found at (median share of nodes) | 97% | 89% | 84% |
| Platform | Mac, Docker | Kaggle, subprocess | Kaggle, subprocess |

- **The size of the held-out splits explains most of the differences.** Where they are large (spooky), validation and the probe agree, the pick is the best node, and the rules have nothing to act on. Where they are small (pizza), both are noisy, the probe is worse than validation, selection costs the most, and the rules fire on noise.
- **Spooky was still improving at 4 hours;** pizza often was not.
- **Pizza carries a label leak in its data** (`giver_username_if_known`), which MLE-bench says makes the task unsuitable; no pick used it.

## What a person could add

- **Not leakage checking:** A1 already prevents validation leakage, and its screen held up in the stress test.
- **Task knowledge:** the spooky C6 session stalled without the naive Bayes plus linear recipe, which an expert or a web search would supply; we had neither, by design.
- **Data checks:** a leak built into the data, like pizza's, is invisible to A1.
- **A direct instruction channel:** in the insults C6 session the participant could choose which node the agent worked on, but not what it changed.
