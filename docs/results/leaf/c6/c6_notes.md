# C6 – Leaf Classification: Human Monitoring Notes

**Task:** leaf-classification
**Condition:** C6
**Seed:** 100
**Session duration:** 120.9 minutes
**Human interventions:** 0

## 1. Session Observations

During the C6 session, I monitored the agent through the dashboard. I could see the different nodes and their validation and probe scores.

I was unsure which changes were significant enough to require an intervention. I did not feel confident choosing a branch to prune, so I allowed the agent to continue without making any changes.

## 2. Human Intervention

No interventions were made during this session.

- Interventions queued: 0
- Interventions applied: 0
- Nodes pruned by the human: 0

## 3. Debrief

**What made me intervene?**

I did not intervene because I was unsure when intervention was necessary.

**What did I ignore?**

I did not act on individual changes in validation or probe scores because I was uncertain whether they indicated a meaningful problem.

**What would have helped me?**

Clearer dashboard guidance would have helped me decide when to intervene, especially when validation loss improves while probe loss becomes worse.

## 4. Final Results

- Nodes explored: 49
- Working nodes: approximately 90%
- Final selected node: n33
- Validation log loss: 0.000885
- Probe log loss: 0.178746
- Test log loss: 0.026057
- Valid submission: Yes
- Above benchmark median: Yes
- Medal: None

## 5. Conclusion

The agent completed the C6 session without human intervention and produced a valid submission. This session showed that deciding when to intervene can be difficult without clear guidance from the dashboard.