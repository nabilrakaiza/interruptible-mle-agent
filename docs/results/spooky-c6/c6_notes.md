# C6 notes: spooky, seed 100

- **Participant:** Nabil, who owns spooky. Has seen the task's 13 grid runs, not this one. Knows the general approach of the competition's top solutions.
- **Assistant:** Claude explained the dashboard during the session (what the signals mean, node scripts on request). It gave no modelling ideas and did not read test scores.
- **Allowed actions:** oversight only (prune, final pick, correct a finding). Steer or add idea only to stop or undo something seen on the dashboard. No outside lookups.
- **Run start:** 10:50 (Colima started 10:50, first LLM call shortly after)
- **Session start (dashboard opened on this run):** the dashboard logged `session_start` at 10:52, two minutes into the run, when the page opened on this run. Watching for real started at: (fill in)

## During the session

| Time | Node on screen | What I said | What I did |
|---|---|---|---|
| 11:08 | n7 | "around 8 nodes, I don't really see anything wrong" | none |
| 11:16 | n1, n0 | "n1 and n0 might still be picked by chance; if a chance pick of n1 shows a big improvement, I'll do something. The current branch is still improving." Noticed: finding f-5f0d824851 says n0 beat n1, but the probe ranks n1 better (0.592 vs 0.616) | none: chose to wait |
| 11:19 | n12 | "the tree from the n2 draft doesn't seem promising, an improvement didn't decrease the score" (n5 0.531 to n12 0.535, about 0.11 behind the best) | none for now: "I'll just leave it for now, probably will prune it later" (decided 11:34) |
| 11:28 | n4 | "should we try to do improvement on n4? it has a fairly similar value to n3, but it doesn't get traversed" | redirect: "Improve it next" on n4, note "n4 close to n3 as a draft (0.469 vs 0.442), never expanded" |
| 11:28 | n17 | "n17 just found a breakthrough" (val 0.421 to 0.382, probe 0.436 to 0.394: the main branch added word-level TF-IDF to its character features, which is n4's idea) | none |
| 11:32 | f-738ab0da36 | "the reason is n17 basically" | correct: replaced the finding with a version citing n17 (word+char worse as untuned drafts, but adding word TF-IDF to the tuned char pipeline gave the largest gain, val 0.421 to 0.382, probe 0.436 to 0.394); why: "n17 contradicts this finding ... the probe confirms it" |
| 11:52 | n27 | "best node is still in the tree from draft 3, and it's still decreasing (n27)" (n27 val 0.366, probe 0.375; the redirected n19 on n4 scored the same as n4, 0.469) | none |
| 12:01 | n0, n1, n2, n4 | "if we are going to prune n2, I think we need to prune n1 and n0 as well ... even if there's an improvement, I don't think it will be that big, and it's always better to just continue from n3" (about 60 min left, main branch at 0.366, the best pruned node 0.469; gave up waiting for a chance pick of n1) | prune n0, n1, n2 (with n5, n12) and n4 (with n19); all applied |
| 12:11 | n30 | "I'm afraid it will get stuck at around 0.36, should I inject something?" Decided against injecting (an expertise action); n30 has the best probe in the run (0.3688 vs n29's 0.3757) but worse validation (0.3661 vs 0.3637) | redirect: "Improve it next" on n30 |
| 12:17 | n37, n11, n23, n38 | Redirect result: n37 (from n30) removed n30's punctuation view "because earlier evidence showed..." and scored the same as n29 (0.3637 / 0.3757). Asked whether to prune n38, n23, n11 (old weak side nodes, 0.42 to 0.47) | prune n11, n22 (with n23), n34 (with n38) and n6; all applied 12:19 to 12:20 |
| 12:30 | n42 | "idk what to do now". n42 is the new best on validation (0.3622) but its probe got worse (0.3829, against n30's 0.3688): the first divergence in the run. Claude checked the C4 rule offline: it would fire here, pruning n37 (anchor n30, validation +1.1%, probe -3.8%, consistent in 98% of bootstrap resamples) | prune n37 (with n42), applied 12:33; reason: "n42 best on validation (0.3622) but probe got worse (0.3829 vs n30's 0.3688): validation and probe diverge since n30". Agrees with the C4 rule |
| 12:43 | n48 | "8 mins left, and no sign of improvement". n48 is the new best on validation (0.3612) and second on probe (0.3733); n30 is still best on probe (0.3688) but 0.005 behind on validation | (final pick pending) |
| 12:46 | n49 | "n49 is slightly better than n48" (val 0.36119 vs 0.36121, probe 0.37321 vs 0.37325: a tie, since n49 only added an archaic-diction feature block) | none: n49 is the default pick; no override |
| 12:49 | n50 | "there's n50 now" (val 0.3623, 0.001 worse than n49; probe 0.3725, 0.0007 better): within noise of n49 | none: kept n49 as the final pick (by validation), after weighing n30 (best probe, 0.3688) |

## Debrief

Written at 12:55, after the run ended at 12:50. The participant's answers, tidied, with details from their messages during the session.

- **What made me intervene?**
  Two kinds of cue.
  - **Contradictions between what the agent believed and what the scores showed.** Finding `f-738ab0da36` said combining word and character features was worse than character-only, but n17 showed the opposite, with the probe agreeing, so I corrected it. The divergence at n42, where validation improved but the probe got worse, led to the n37 prune.
  - **Time running low.** With about an hour left, I pruned early branches (n0, n1, n2, n4, then n6, n11, n22, n34). They had been explored little because their scores were low, and with the main branch about 0.1 ahead I didn't think they could catch up in the time left.

  The redirects (n4, n30) were attempts to explore nodes that greedy search kept skipping. Neither produced a gain. n19 matched n4's score, and n37 undid n30's change.
- **What did I ignore on purpose?**
  - **The first part of the run.** I let the agent write all its drafts and start improving before judging anything.
  - **The weak branches.** I noticed the n0/n1 probe reversal at 11:16 and that the n2 branch was stalling at 11:19, but chose to wait rather than act on one or two nodes.
  - **Plateaus on the main branch.** I didn't step in while it improved slowly, since validation and probe agreed.
- **What would I have wanted to see?**
  - **Whether a bigger gain was possible.** I expected a big drop at some point and a final score close to the C1 runs, but the run plateaued around 0.36, above the C1 runs' 0.29 to 0.36. It's worth looking at the C1 runs where scores dropped sharply, to see what caused the drops and whether a monitor could spot or encourage them.
  - **From the session, things the dashboard didn't show me:**
    - how likely a node is to be picked again (I asked whether n0 and n1 could still be explored);
    - what a redirect will actually do (n37 reverted the change I wanted explored);
    - a way to cancel a queued action (the n4 redirect became redundant after n17).
- **Overall.** I don't have the ML expertise to add meaningful new ideas or drafts through inject. So I limited myself to oversight, judging the agent's own attempts using validation, probe and its findings.

## After the session (results, test scores now allowed)

- **Final submission:** n49, test **0.3684** (valid, above median, no medal). It ranks 2nd of 35 working nodes on test. The best is n48 at 0.3683, so C2 (oracle) = 0.3683 and C3 (top 3) = 0.3683.
- **n49 or n30:** n30, the best on the probe, scored 0.3723 on test, 0.004 worse than n49. Keeping n49 was right, and n30's low probe was mostly luck.
- **The n37 prune:** n42 scored 0.3781 on test against n37's 0.3730, so the divergence was real and the probe was right. It probably didn't change the final pick, though: n48 and n49, on another branch, later beat n42 on validation anyway.
- **The n0/n1 reversal:** on test n0 (0.6093) beat n1 (0.6353), so finding `f-5f0d824851` was right and the probe's reversal was noise. Waiting was the right call.
- **Agreement with the C4 rule** (`scripts/replay_policy.py`): the rule fires once, after n42, pruning n37, the same prune made here.

  | | C4 prunes | C4 does not prune |
  |---|---|---|
  | **Person prunes** | 1 (n37, the divergence at n42) | 8 (n0, n1, n2, n4, n6, n11, n22, n34: budget cues, far behind with little time left) |
  | **Person does not prune** | 0 | the rest |

- **Interaction cost** (`scripts/interaction_cost.py`): 12 interventions, all applied (9 prunes, 2 redirects, 1 correction), the first at 37% of the budget. The script's 100 human minutes is the span from opening the dashboard to the last action. The participant checked in about every 10 minutes, so actual attention was much less.
- **Against C1:** C6's 0.3684 is worse than every C1 seed (0.3606, 0.3087, 0.2946). With one session on a different seed, this can't separate the effect of the interventions from seed noise.

## Limitations to report

- **Not an ML expert.** The participant is a student, not an experienced Kaggle or MLE practitioner, so their judgement (which branches to prune, which node to submit) may be worse than an expert's. C6 shows what a non-expert monitor does with the dashboard, not the best a human monitor could do. (Raised by the participant during the session, 12:05.)
