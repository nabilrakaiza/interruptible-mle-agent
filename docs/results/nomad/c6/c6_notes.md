# C6 Human-in-the-Loop Session — NOMAD2018

## 1. Session Information

- **Task:** nomad2018-predict-transparent-conductors
- **Condition:** C6 — Human intervention
- **Seed:** 100
- **Budget:** 2 hours
- **Model:** DeepSeek V4 Flash 0731
- **Evaluator:** A1
- **Human participant:** Task owner
- **Prior familiarity:** The participant had previously completed and analyzed the 13 automated NOMAD2018 runs.

## 2. Session Observations

| Elapsed time | Nodes observed | Observation | Action |
|---|---|---|---|
| 12 min | n6, n8, n9, n10 | n10 had the best validation score (0.06238), with probe score 0.06448. Some branches performed worse, but there was insufficient evidence to intervene. | Continued observing |
| 21 min | n17, n20, n22 | n20 failed, and its debugged descendant n22 had substantially worse validation and probe scores than n17. | Investigated n22 |
| ~30–35 min | n22 | n22 had validation 0.08877 and probe 0.09089, compared with n17's 0.06281 and 0.06483. | Pruned n22 and its subtree |
| 60 min | n10, n25 | n25 improved validation to 0.06224, but its probe score (0.06549) was worse than n10's (0.06448). | No intervention |
| 107 min | n54 | The best validation score improved to 0.06182, while the corresponding probe remained 0.06549. | No further intervention |

## 3. Human Intervention

**Action:** Prune node n22 and its subtree.

**Queued:** 29 October 2026, 08:58:44 SGT

**Applied:** 29 October 2026, 08:59:37 SGT

**Outcome:** Successfully applied.

**Reason:** The debugged model substantially worsened both validation and probe performance relative to ancestor n17. Other available branches had produced substantially better-performing models, so further exploration of n22 appeared unpromising.

The intervention was based on poor performance on both metrics, not on validation improvement accompanied by probe deterioration.

## 4. Comparison with the Automated C4 Policy

The post-hoc C4 replay reported zero automatic pruning interventions on the C6 trajectory.

The human participant pruned n22 because both validation and probe performance deteriorated. The C4 divergence-pruning rule specifically targets situations where validation improves while probe performance worsens.

This suggests that human judgment may identify unpromising branches using criteria not captured by the current C4 rule.

The replay result should be interpreted cautiously because the trajectory already contains the human intervention.

## 5. Interaction Cost

| Metric | Result |
|---|---|
| Human interventions queued | 1 |
| Successfully applied | 1 |
| Dropped | 0 |
| First intervention timing | 34.8% of node progress |
| Recorded human time before intervention | 9.7 minutes |
| Recorded abandoned-node wall-clock cost | 0 seconds |

The recorded human time measures the dashboard interaction interval before the intervention, not necessarily the participant's total attention throughout the two-hour session.

## 6. Final Outcome

- **Total nodes:** 89
- **Final selected node:** n83
- **Official MLE-bench score:** 0.06137
- **Submission validity:** Valid
- **Above competition median:** Yes
- **Medal:** Silver

The C6 score was lower than the three-seed C1 mean of 0.06229. However, this single human-intervention session does not establish that the intervention caused the improvement.

## 7. Debrief

**What prompted intervention?**

A debugged model showed a substantial deterioration in both validation and probe scores relative to its ancestor. The participant considered the branch unlikely to produce a competitive model.

**What was deliberately ignored?**

Individual unsuccessful model attempts and small validation–probe differences were not treated as sufficient evidence for pruning. The participant allowed the agent to continue exploring several competitive branches.

**What additional information would have been useful?**

Clearer visualization of within-lineage validation–probe trends, intervention effects, and whether a poor-performing branch was likely to be explored again.

## 8. Limitations

- Only one human-supervised session was conducted for NOMAD2018.
- The participant was familiar with previous runs on the same task.
- No separate observer recorded the think-aloud process.
- The session experienced an internet connectivity interruption and a temporary execution stall.
- The intervention was informed by dashboard observations and external discussion, so it should not be described as an entirely unaided decision.
- The automatic C4 replay reported no interventions, but its interpretation requires care.
- The annotated trajectory report was not generated because of a Windows text-encoding error.