# Spooky: all results of the half plan

The half plan's 13 runs on `spooky-author-identification`: seeds 0, 1 and 2 of C1, C4 and C5, and seeds 0 and 1 of A1-off and A4-off. They ran over three nights, 25 to 28 Oct 2026, on Nabil's Mac. Each night has its own write-up:

- [`spooky-seed0.md`](spooky-seed0.md): all five conditions, seed 0
- [`spooky-seed1.md`](spooky-seed1.md): all five conditions, seed 1
- [`spooky-seed2.md`](spooky-seed2.md): C1, C4 and C5, seed 2
- [`spooky-c6.md`](spooky-c6.md): the C6 live session, seed 100
- [`spooky-drops.md`](spooky-drops.md): where the big drops come from, across all 14 runs

Spooky is multiclass log loss, so **lower is better**. MLE-bench thresholds: median 0.4188, bronze 0.2938.

## Setup

- DeepSeek V4 Flash 0731 (fp8), Docker sandbox, 2 hours and 2 CPUs per run, A1 on unless the condition turns it off.
- From seed 1 onwards, with the PR #7 fix for `OUTPUT_DIR` statements. It crashed two nodes in seed 0's A4-off run and none after.
- **Cost:** $1.00 for the 13 runs ($0.294, $0.446 and $0.256 a night).
- **Health:** no restarts. Every run finished on its budget and made a valid submission.

## Test scores

| Condition | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---|---|---|---|
| C1 | 0.3606 | 0.3087 | 0.2946 | **0.3213** |
| C2 (oracle, from C1) | 0.3606 | 0.3087 | 0.2946 | 0.3213 |
| C3 (top 3, from C1) | 0.3606 | 0.3087 | 0.2946 | 0.3213 |
| C4 | 0.3808 | 0.3339 | 0.3568 | 0.3572 |
| C5 | 0.3632 | 0.2973 | 0.3414 | 0.3340 |
| A1-off | 0.3377 | 0.3374 | n/a | 0.3375 |
| A4-off | 0.3361 | 0.3651 | n/a | 0.3506 |

- **All 13 runs are valid and above the median. None reached bronze.** The closest were C1 seed 2 (0.2946, 0.0008 short) and C5 seed 1 (0.2973), whose tree held a bronze-level node it didn't pick.
- **C2 and C3 equal C1 on every seed:** C1 always submitted its best node on test.
- **No condition is clearly better than another.** C1 alone ranges over 0.066 across seeds, more than the gap between any two conditions' means. The full table with bootstrap intervals is in [`spooky-seed2/outcomes/summary.md`](spooky-seed2/outcomes/summary.md).

## Interventions

| Runs | Fired | Effect on the submission |
|---|---|---|
| C4, seeds 0 to 2 | never | none |
| C5, seeds 0 to 2 | once (seed 2, safe point 35) | none |
| C4 rule replayed on A1-off seed 1 | at n45 | **test 0.337 to 0.314** |

- **C4 never fired in a live run.** With A1 on, validation and probe moved together, so the divergence it watches for never happened. C4's runs are therefore C1's agent on other random paths. That C4 is worst on all three seeds is noise, not pruning.
- **C5 fired once,** at safe point 35 of seed 2. It deleted a finding that character n-grams hurt. The probe agreed they hurt, just by less (−0.036 against −0.058 on validation), and the gap was 0.022 against a 0.02 threshold. This reads as a false positive of the rule's check for "hurts" findings. It changed nothing: the pick was already made, and the agent never tried character n-grams again.
- **Replayed after the run, on A1-off seed 1, C4 would have helped.** It fires at n45, prunes the 12 nodes after it, and the pick becomes n43 at test 0.3144 instead of 0.3374, a gain of 0.023. A1-off runs without policies, so this is a replay, not a measured condition.

## C6 live session

One session, seed 100, oversight only ([`spooky-c6.md`](spooky-c6.md)). Test **0.3684**, 0.0001 from the run's best node, and worse than every C1 seed.

- **12 interventions:** 9 prunes, 2 redirects and 1 finding correction.
- **The C4 rule:** replayed over the session, it fires once (n37, after n42's divergence), the same prune the participant made. The participant's other 8 prunes followed a budget cue the rule doesn't have: a branch far behind the best with little time left.
- **Both redirects produced nothing:** a redirect chooses which node to improve, not what the agent changes.
- **The probe-best node (n30) was worse on test** than the validation-best pick.

## Main findings

1. **A1 kept validation honest.** In the 11 runs with A1, the pick's test score stayed within 0.015 of its validation score. Without A1, the gap was 0.023 on seed 0 and **0.132 on seed 1**. On seed 1 the agent stacked its models with a logistic regression fitted on its own validation split and scored on that same split. Validation fell to 0.205 while test stayed at 0.337, and the submitted node ranked 27th of 55 on test.
2. **Interventions only have work when the agent's own signal breaks.** With A1, the scripted monitors found nothing to prune and one finding to correct, wrongly. Without A1, the C4 rule, replayed, would have caught the leak and recovered 0.023.
3. **Final selection rarely matters with A1.** Across the C1, C4 and C5 runs, the oracle pick would have gained 0.001 at most, except on C5 seed 1. There it would have gained 0.004 and reached bronze (0.2934 against 0.2973), picking from a near-tie on validation. Without A1, on seed 1, the oracle would have gained 0.023.
4. **The leakage check caught two leaks with A1 on.** In C1 seed 2, it stopped two scripts (n15 and n38) that evaluated a model on validation rows it was fitted on, and debug fixed both.
5. **Seed noise dominates.** Three seeds, or two for the ablations, can't separate effects of a few hundredths when C1's own seeds differ by 0.066.
6. **The big drops come from combining naive Bayes with a linear model** ([`spooky-drops.md`](spooky-drops.md)). Every run below 0.34 submitted such a combination, and every run that didn't stayed at 0.34 or above. Adding one ComplementNB to C6's submitted script improves its test score from 0.368 to 0.336. C6's agent had kept a finding that said to prefer TF-IDF over NB: true for the two drafts it compared, but wrong for what mattered later.

## Pick's validation against test

| Run | Validation | Test | Gap (test − validation) |
|---|---|---|---|
| C1 seed 0 | 0.3547 | 0.3606 | +0.006 |
| C1 seed 1 | 0.3148 | 0.3087 | −0.006 |
| C1 seed 2 | 0.2954 | 0.2946 | −0.001 |
| C4 seed 0 | 0.3690 | 0.3808 | +0.012 |
| C4 seed 1 | 0.3200 | 0.3339 | +0.014 |
| C4 seed 2 | 0.3574 | 0.3568 | −0.001 |
| C5 seed 0 | 0.3676 | 0.3632 | −0.004 |
| C5 seed 1 | 0.2917 | 0.2973 | +0.006 |
| C5 seed 2 | 0.3555 | 0.3414 | −0.014 |
| A4-off seed 0 | 0.3214 | 0.3361 | +0.015 |
| A4-off seed 1 | 0.3712 | 0.3651 | −0.006 |
| **A1-off seed 0** | 0.3149 | 0.3377 | **+0.023** |
| **A1-off seed 1** | 0.2051 | 0.3374 | **+0.132** |

## Limitations

- Few seeds, and 2-hour runs on 2 CPUs; scores were still improving at the end of most runs.
- One model, and no pretrained models offline.
- C4 and C5's thresholds came from a handful of pilots. C5's check on "hurts" findings treats a smaller harm on the probe as a failure (see above).
- C4's gain without A1 is a replay. A condition combining A1-off with C4 isn't in the grid.
- We are not ML experts, so our C6 judgement may be worse than an expert's. An expert might have spotted that C6's agent was avoiding naive Bayes, a gap worth about 0.03 on test.
- **Spooky is public.** It is an old Kaggle competition, so its winning approaches are online, and may be in the model's training data. That is why the participant did not search online during the session. On tasks whose solutions are not public, such as a private held-out set in the spirit of Humanity's Last Exam, both the agent and the monitor could be allowed to search, with no risk of copying a known answer. More resources could give both of them more insight, and a fairer test of what a human adds.

## Next

- **After the half plan:** C5 could require the probe to disagree in direction before deleting a "hurts" finding, and A1-off with C4 could become a real condition.
