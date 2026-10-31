# Presentation Q&A prep

Likely questions after the 12-minute presentation, with short answers based on our results. The numbers come from `docs/results/` (half plan; spooky seeds 0 and 1 also at 4 hours). Lead with the first one or two sentences, and use the rest only if asked to go further.

## About the setup

### 1. Have you compared with Claude Code or Codex?

> Our question isn't which agent scores best. It's which human interventions help an agent, and what they cost. To measure that, we need things a general coding agent doesn't expose: a search tree with scored nodes, a frozen evaluator the agent can't touch, a probe split only the monitor sees, and safe points where an intervention is applied. Claude Code and Codex work as a single conversation, so an intervention there is just another chat message, with no tree to prune and no held-out probe to compare against. Cost mattered too: we ran over 50 grid runs at about 8 cents each, and a frontier coding agent costs many times more per run.

If they push further:
- **We control everything except the intervention.** Every condition uses the same model, harness, budget and sandbox, and only the intervention changes. Swapping the agent would change everything at once.
- **Fairness matters more than strength.** A stronger agent might score higher, but the question is whether interventions change the outcome *relative to the same agent left alone*.
- **Contamination affects every model, ours included.** These are old Kaggle tasks, so any model may have seen solutions in training. Blocking web access doesn't fix that, which is why future work moves to unpublished tasks.
- **The fair version of the question is our future work:** the same agent with other models, or the same intervention protocol on another tree-search agent such as the original AIDE.

Avoid saying:
- "We can't stop them using the internet." Both can run with web access off.
- Cost as the main reason. It's real, but weaker than the methodological reason, so say it last.

### 2. Why DeepSeek V4 Flash and not a stronger model?

> We needed many runs: 52 grid runs plus live sessions in the half plan, and about 126 in the full plan. DeepSeek V4 Flash was the cheapest model that wrote reliable long ML scripts. We tried free models first, and they hit rate limits or ended their free tiers. It costs about 8 cents per 2-hour run, and our MiniMax pilot scored similarly at about twice the price. What matters for us is that every condition uses the same model.

### 3. Why build on AIDE and not MCTS or another search?

> AIDE is the simplest widely used design: a greedy tree of scripts, and the baseline in MLE-bench. A tree with scored nodes is what makes interventions like pruning and choosing the final node meaningful. More complex search would add variation that has nothing to do with the interventions. Testing the same interventions on other search strategies is a natural next step.

### 4. Isn't the probe just a second validation set? Couldn't the monitor overfit it?

> Yes, it can be overfit if it's used to choose, which is why only the monitor sees it and the agent never optimises it. We saw that risk in the spooky session: the node with the best probe score (n30) was 0.004 worse on test than the agent's own pick, because the best of about 45 noisy probe scores is optimistic. The probe is most useful for spotting a *trend*, validation improving while the probe gets worse over several nodes, not for ranking single nodes.

### 5. Why use public Kaggle tasks if the model may have seen the solutions?

> They're the standard benchmark (MLE-bench), with known medal thresholds, so our scores mean something. Contamination would affect every condition equally, since they all use the same model, so it doesn't bias the comparison between interventions. To keep the live sessions fair, we didn't search online during them. Unpublished tasks are in our future work.

## About the results

### 6. Seeds vary more than conditions. So what can you actually conclude?

> We can't rank the conditions on average score, and we say so: on spooky, C1's own seeds differ by 0.066, more than any gap between conditions. What we *can* conclude comes from looking inside the runs: where validation and probe moved apart, what each intervention did there, and what the oracle pick would have gained. Those findings are consistent across tasks. The full plan adds seeds to tighten the averages.

### 7. Why did the C4 prune rule almost never fire?

> Because with A1 on, the agent's validation was rarely misleading. Validation and probe moved together on spooky and cactus. C4 fired live only on nomad. Replayed, it fires on spooky's leaking A1-off run, where it would have improved test by 0.023 at 2 hours and by 0.094 at 4 hours. We see that as a result in itself: the prune helps when the signal breaks, and stays quiet otherwise.

### 8. Is C4 too strict? It stayed silent on some clear-looking drops.

> It's strict on purpose. It needs the probe drop to hold in 95% of bootstrap samples. On tasks with tiny probe splits, like leaf with 89 rows for 99 species, one row can swing the probe score, and a looser rule would act on noise. It also had small false alarms: replayed on spooky C5 seed 1 it would have cost 0.0035. A rule tuned for small probes is in our future work.

### 9. Is correcting the agent's findings (C5) useless?

> In our runs it didn't help. It fired on false positives, like a finding the probe actually confirmed, and on findings that cited crashed nodes. The most important finding we saw, "prefer TF-IDF over naive Bayes" in the spooky session, was true for the two drafts it compared, but it steered the agent away from the combination the best runs used. Adding one naive Bayes model to that run's final script improves test from 0.368 to 0.336. No simple rule catches that, and it needs ML expertise.

### 10. Isn't the A1-off leak just a bug in one script?

> It's the same failure the literature describes: the agent fits something on its own validation data and then scores itself on it. It happened in both spooky A1-off seeds, and in nomad A1-off on a smaller scale. Given more time it got worse: spooky seed 1's gap between validation and test grew from 0.13 at 2 hours to 0.26 at 4 hours. With A1 on, the agent can't do this, because it never sees the validation labels.

### 11. Does more time help?

> With A1, yes. Extending spooky's seeds 0 and 1 from 2 to 4 hours left all 8 runs the same or better, by up to 0.041, and C5 seed 1 reached bronze. Without A1, both runs got worse, because the extra time went into overfitting validation.

### 12. Why does one prediction decide the score on leaf?

> Leaf has 99 species and only 178 validation rows, so good models are about 99% accurate and score close to zero on validation. Log loss heavily punishes a confident wrong answer, so the one or two hard leaves in test decide the score. That's also why the final pick matters most on leaf: the oracle pick cuts C1's loss by about a third, against under 2% on the other tasks.

### 13. What are C2 and C3 for?

> They're post-hoc reference points, computed from C1's own tree. C2 picks the node with the best test score, an upper bound on what a perfect final pick could gain. C3 picks the best of the top three by validation, a simple hedge. They show how much is lost in the final pick alone, apart from the search. That was almost nothing with A1 on most tasks, but a lot on leaf.

## About the live sessions

### 14. Four sessions by team members: what can you really claim?

> Only qualitative findings, and we treat them that way, as the proposal planned. We were all non-experts, we knew the agent, and we had seen other runs on our task. The sessions show what cues a person uses (budget, wrong model family, regressions), that 17 of 18 prunes removed weak branches, and that a check every ten minutes caught the one real problem on spooky. A proper user study with outside and expert participants is future work, starting with the replay demo.

### 15. Why didn't the leaf participant intervene at all?

> Validation was close to zero for most of the run while the probe stayed around 0.1 to 0.3. So there was always a gap, and it never pointed at one node. That's a useful finding: the dashboard helps when the gap *changes*, and gives no cue when it's large all the time. The participant asked for clearer guidance on when to act.

### 16. Why not let people inject their own ideas?

> Injecting ideas would have measured our ML knowledge rather than oversight, and we aren't experts. We kept to actions that judge the agent's own work: prune, redirect, choose the final node and correct a finding. The spooky naive Bayes example shows where an expert could add real value through an injected idea. That's why expert monitors are in our future work.

### 17. How did you measure interaction cost?

> From the logs. Every intervention is queued with a timestamp and recorded as applied or dropped, and the dashboard logs when a person opens it and looks at a node. That gives the number of interventions, when they happened, and how long people spent. On spooky, a check every ten minutes of a minute or two each was enough. On cactus the participant watched the whole run, and still made no change to the final submission.

## About the takeaway

### 18. What should someone building an MLE agent take from this?

> First, lock the evaluator so the agent can't fit or redefine its own score. It's the single most important safeguard in our results. Second, give a monitor a held-out signal like the probe. The useful moment to step in is when validation keeps improving while the probe gets worse. Third, the final pick deserves attention on tasks with small validation sets. Light, occasional oversight is enough. There's no need to watch every step.

### 19. How much did the whole study cost?

> About $1 to $2 per task for the 13 half-plan runs, plus a few cents per live session, and about 40 cents per night for extending runs to 4 hours. The main cost was laptop time: about 26 machine-hours per task for the half plan, run overnight.
