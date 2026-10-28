# C6 notes: cactus, seed 101

- **Participant:** Dziand, who owns cactus. Has seen the task's 13 grid runs, and the result of an earlier, unwatched C6 run (seed 100, test 0.99989), not this one.
- **Assistant:** Claude started the run, explained the dashboard and node scripts, and, when asked "what intervention should I make?", **suggested interventions** (which nodes to prune and why). The participant chose which suggestions to take and typed the reasons. Claude did not read test scores until the run ended.
- **Allowed actions:** oversight only (prune, final pick, correct a finding). Steer or add an idea only to stop or undo something seen on the dashboard. No outside lookups.
- **Why seed 101, not 100:** seed 100 ran from 14:23 to 16:23 the same day but was not watched. The dashboard was opened once (14:31, on n0) and left, because the participant thought the run took 4 hours. It was kept as it is, with 0 interventions, and this run was started on the next seed after a restart of the Mac to clear swap.
- **Machine:** 13-inch MacBook Pro (2022, Apple M2, 8 cores, 8 GB), macOS 14.1.1, on power and kept awake (`caffeinate`). Docker ran in Colima with a 2-CPU, 5 GB VM; each script's sandbox was capped at 2 CPUs and 4 GB. Training was on CPU only.
- **Run start:** 19:14 (Colima started 19:13; first LLM call, retrieval, finished 19:15)
- **Session start (dashboard opened on this run):** the dashboard logged `session_start` at 19:18 and again at 19:20 (page reloaded). Watching for real started at 19:20, with the tree still empty: the first node (n0) appeared at 19:27, 13 minutes after the start.

## During the session

Times of messages are from the run's checkpoints (elapsed minutes on screen); times of actions are from `queue.jsonl` and `dashboard_log.jsonl`.

| Time | Node on screen | What I said | What I did |
|---|---|---|---|
| 19:20 | none (checkpoint 0) | "why does the dashboard look like this?" (0 nodes, 0 min elapsed, "Tree is empty") | none: the first coding call was still running (seed 100's took 4 minutes too) |
| 19:27 | n0 | (looked at the first draft) | none |
| ~19:56 | n0 to n9 | "what intervention should I make for this? any idea?" (10 nodes, 42 min elapsed, best n8 val 0.9996, probe 0.9996). Claude listed: prune the four non-CNN drafts, redirect to n8, end the run, or do nothing | none yet |
| 20:03 | n0 | "should I write the n0, n1, n3, n4 here on the why?" and "where can we know that it is not using CNN?" (Claude showed the plans and scripts: n0 logistic regression, n1 PCA + logistic regression, n3 ExtraTrees, n4 sklearn MLP; only n2 is a CNN). "yes, image processing without CNN is awful" | prune n0, n1, n3, n4 (20:03:54 to 20:05:02), reason "not a CNN model"; applied 20:03:57 (n0) and 20:05:58 (the other three) |
| 20:06 | Interventions tab | "is queue means that it is submitted to be pruned?" | none |
| 20:10 | n8 | "please also mention the device used for training" (in the write-up) | none |
| ~20:15 | n8, n9, n10 | "should I prune n8? because it creates 2 subtrees with val and probe less high" (n9 0.9995, n10 0.9994 against n8's 0.9996). Claude: no, n8 is the best node and the pick, and a prune removes it with its subtree | none: kept n8 |
| ~20:21 | n11 to n15 | "anything to intervene?" (67 min elapsed). n13 (residual blocks) new best by 0.00002; n11 had repeated n7 exactly (BatchNorm, 0.9992118 both); n12 (mixup) 0.9970 and n15 (input normalisation) 0.9972 well below n7 and n11 | prune n15 (20:27:14), "it is a regression and not worth extending"; prune n12 (20:27:28), "it is a regression, not worth extending"; both applied 20:27:50, with n15's children n16 and n18 |
| ~20:33 | n5, n17, n19, n13 | "anything to intervene?" (79 min elapsed). The agent was extending the n5 branch (TTA on the no-BatchNorm CNN): n17 0.9943, n19 0.9937. Claude suggested pruning n5 (with n17, n19) and n6 | none: chose to wait |
| 20:42 | n20, n21, n22 | "now, analyse the condition. anything should I intervene?" (87 min elapsed, 33 left). The n5 branch climbed: n20 (SiLU) 0.9950, n21 (GroupNorm) 0.9990; n22 crashed (`GroupNorm(8, …)` on the 3-channel input) and was about to be debugged | prune n22 (20:44:07), "debug the weak branch" (meaning: don't spend a debug step on the weak branch); prune n5 (20:44:44), "focus on n8 and n13"; both applied 20:46:05, removing n17, n19, n20, n21, n22, n23 and n24 too |
| 20:58 to 21:01 | n23, n9, n10, n14 | (looked at the debug of n22 and n8's and n13's children) | none: no final override; n13 stays the pick |
| 21:18 | final tree | "I think the training is already done, right?" (the run ended at 21:15, 31 nodes) | none |

## Debrief

Written after the run, from the participant's messages during the session (no separate debrief was held).

- **What made me intervene?**
  Three kinds of cue.
  - **The wrong model family for images.** Four of the five drafts flattened the 32×32 images into pixel vectors (logistic regression, PCA, ExtraTrees, an MLP) and scored 0.94 to 0.97, while the one CNN reached 0.9996 through its improvements. "Image processing without CNN is awful", so I pruned them.
  - **Regressions.** n12 and n15 scored well below the nodes they were meant to improve on, so I didn't want the search to extend them.
  - **Little time left on a weak branch.** With 33 minutes left, the n5 branch was still below the best, and its newest node had crashed. I pruned the crash so no debug step was spent on it, then the branch, to focus on n8 and n13.
- **What did I ignore on purpose?**
  - **n8's children being worse than n8.** I first wanted to prune n8 for that, then kept it: they were attempts that didn't help, not a sign that n8 was bad.
  - **The n5 branch at 20:33.** Claude suggested pruning it then; I waited, and it climbed from 0.994 to 0.999 before I pruned it 11 minutes later.
  - **n6**, a weak leaf (0.9918) that Claude also suggested pruning. I left it, and the search spent its last steps there.
  - **The final pick.** n13 and n8 were tied on validation (0.99965 against 0.99963), so I didn't override.
- **What would I have wanted to see?**
  - **Progress before the first node.** For about 13 minutes the dashboard showed "Tree is empty" and 0 min elapsed, which looked like a stuck run.
  - **What the agent would do next,** so a prune can be judged against where the search is actually going (the n5 branch got most of the steps between 20:20 and 20:45).
  - **Duplicates.** n11 repeated n7 exactly, and I only saw it when told.
- **Overall.** The run was healthy all along: validation and probe agreed within 0.0031 on every working node, and the best reached 0.9996 after 33 minutes (n8, 19:47). My interventions were about not wasting steps, not about fixing anything. I asked the assistant for suggestions throughout, and every prune I made was one it had suggested, so these choices are not mine alone.

## After the session (results, test scores now allowed)

- **Final submission:** n13, test **0.99953** (valid, above median, no medal: every medal needs 1.0). It ranks 3rd of 14 working nodes on test. The best are n8 and n29, both 0.99956, so C2 (oracle) = 0.99956 and C3 (top 3: n13, n8, n29) = 0.99956. The pick lost 0.00003, a tie on validation broken by noise.
- **n29 is n8 again.** After the n5 prune, the search spent its last steps on n6: n25 added BatchNorm, n28 removed the augmentation, n29 doubled the filters. n28 and n29 have exactly n7's and n8's scores on validation, probe and test. The last ~25 minutes rebuilt the main line from another node and found nothing new.
- **The prunes, judged on test:** none of the 16 pruned nodes beat the pick. The best of them were n18 (0.9981, on n15's branch) and n21 (0.9980, on n5's). So no prune cost anything, and none changed the pick: n13 was the best on validation from the moment it appeared (20:14) to the end.
- **Two prunes came too late to save a step.** Prunes apply between nodes. n15's children n16 and n18 had already run when its prune applied (20:27), and n22's debug (n23) and n21's child n24 had already run when the n22 and n5 prunes applied (20:46). The n22 prune saved no debug step; the n5 prune moved only the last five nodes (n25 to n29) elsewhere.
- **n15 was not a regression from its parent.** It improved on n2 (val 0.9927 to 0.9972, probe 0.9898 to 0.9958). It was a regression only against its siblings n7 and n11 (0.9992), which add BatchNorm. The reason I typed is right about the branch, wrong about the parent.
- **Keeping n8 was right:** it is joint best on test (0.99956). Pruning it would not have changed the pick (n13 is on another branch), but it would have removed the best node on test.
- **Agreement with the C4 rule** (`scripts/replay_policy.py`): the rule fires 0 times, on this run and on seed 100.

  | | C4 prunes | C4 does not prune |
  |---|---|---|
  | **Person prunes** | 0 | 8 (n0, n1, n3, n4: wrong model family, far behind; n12, n15: regressions against the best line; n22: a crash on a weak branch; n5: a branch behind with little time left) |
  | **Person does not prune** | 0 | the rest |

- **Interaction cost** (`scripts/interaction_cost.py`): 8 interventions, all prunes, all applied, the first at 35% of the run's nodes. The script's 84 human minutes is the span from opening the dashboard (19:20) to the last action (20:44). I was watching throughout, asking about the dashboard every 10 to 20 minutes.
- **Against C1 and seed 100:** C6 seed 101's 0.99953 is within C1's seed range (0.99917 to 0.99994) and below its mean (0.99963). Seed 100, with no interventions, scored 0.99989. With one watched session, this can't separate the effect of the interventions from seed noise, and on cactus the interventions had nothing to fix.

## Limitations to report

- **The assistant suggested the interventions.** Unlike spooky's session, where the assistant gave no modelling or intervention ideas, every prune here was first suggested by Claude, and the participant decided whether and when to take it (and declined two: n6, and n5 the first time). The session measures a person with an AI adviser at the dashboard, not a person alone.
- **Seed 101, not 100.** The protocol's seed 100 ran unwatched; its result was known before this session.
- **Session started before the drafts were done.** The dashboard was open from 19:20, before the first node, against the protocol's "after the drafts".
- **A ceiling task.** Every working CNN node is within 0.001 of a perfect AUC, so no intervention could change the outcome by more than noise.
- **"Not a CNN" is not always a dead end.** In seed 100 the agent's improve step turned the sklearn MLP draft (n1, 0.941) into a CNN (n5, 0.9991). Pruning non-CNN drafts removes that route, which cost nothing here because the CNN draft n2 was already strong.
