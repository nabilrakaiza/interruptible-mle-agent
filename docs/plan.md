# Work plan

Written 9 Oct 2026. Replaces the build dates in section 7.3 of the proposal; the run window, presentation and report dates are unchanged.

We are behind: the first milestone (baseline agent and a pilot C1 run) was due 11 Oct and the agents are still stubs. The run window cannot shrink, because 126 runs of up to 4 hours is about 500 machine-hours, or roughly 5 days on four laptops running non-stop. So the build is what gives: we cut scope and change the build order.

Assumes the earliest presentation slot (29 Oct). A later slot becomes buffer.

## How we build

Get one end-to-end run working first, then widen it. Do not build four parts separately and integrate at the end. The shared contracts (`tree.py`, `intervention.py`, `checkpoint.py`) already exist, so everyone can work in parallel against them.

## Milestones

| Dates | Milestone | Done when |
|---|---|---|
| Fri 9 to Sun 11 Oct | Walking skeleton | One C1 run on `spooky-author-identification` finishes, is graded, and shows up in the dashboard |
| 12 to 15 Oct | Full agent | A short C1 run works on all six tasks, and a queued prune changes the tree |
| 16 to 18 Oct | Freeze | A 4-hour run completes on every machine; C4 and C5 policies run; no code changes after Sunday night |
| 19 to 20 Oct | C1 runs (30) and C6 sessions | C1 trees saved; C4/C5 thresholds fixed |
| 21 to 26 Oct | C4 and C5 (60 runs), then A1-off and A4-off (36 runs) | All trees in shared storage |
| 27 to 28 Oct | Buffer | Reruns done, stress tests done |
| 29 Oct to 12 Nov | Analysis and presentation | Every table regenerates from saved runs |
| 13 Nov | Final report | Submitted |

Run order is by importance: C1, C4, C5, A1-off, A4-off. C6 sessions happen while C1 runs, because the C4/C5 rules are derived from them.

Everyone accepts the Kaggle competition rules today. Data preparation blocks all four roles and needs each person's own account.

## Roles

Names are not assigned yet. The core agent role is on the critical path this weekend, so it goes to whoever can commit the most hours.

| Role | Member | Owns |
|---|---|---|
| 1. Infrastructure and experiments | TBD | `scripts/`, `sandbox.py`, `llm_log.py`, `configs/` |
| 2. Core agent (A3, A5) | TBD | `controller.py`, `agents/coding.py` |
| 3. Evaluation and memory (A1, A4) | TBD | `agents/evaluation.py`, `agents/reflection.py`, `policies/finding_correction.py` |
| 4. Interaction layer | TBD | `dashboard/app.py`, `intervention.py`, `checkpoint.py`, `policies/divergence_prune.py` |

### 1. Infrastructure and experiments

Makes it possible to run anything, then runs everything.

- **9 to 11 Oct:** Install MLE-bench and prepare the six datasets, with setup steps the other three can follow. Write the sandbox function: run a script with a timeout and return output, exit code and wall time. Write the LLM wrapper that logs every call. Add the `.env.example` that the README mentions.
- **12 to 15 Oct:** Grade each node's submission with MLE-bench to fill `test_score`. Write a launcher that runs a (condition, task, seed) grid and resumes after a crash. Estimate API cost from the pilot.
- **16 to 18 Oct:** One full 4-hour run per machine. Move the sandbox to Docker with no network if time allows.
- **19 to 28 Oct:** Own the run schedule: which machine runs what, collecting `runs/` into shared storage, and rerunning failures.

### 2. Core agent (A3, A5)

The search itself: the loop that asks the LLM for a script, runs it, scores it and decides what to try next.

- **9 to 11 Oct:** Controller loop with draft only: generate, execute, score, add to tree, checkpoint, stop on budget, submit the best node.
- **12 to 15 Oct:** Debug and improve operators, the selection rules already in `configs/base.yaml`, findings and model cards in the prompt, and the three final-selection modes.
- **16 to 18 Oct:** Call the intervention-apply function at each safe point. Fix whatever the 4-hour runs expose.
- **19 to 28 Oct:** On call for agent bugs. Code failed nodes into the error taxonomy.

### 3. Evaluation and memory (A1, A4)

Decides how solutions are scored, and what the agent remembers.

- **9 to 11 Oct:** Hand-written train/validation/probe split and scorer for `spooky-author-identification`. Agree with role 2 on how a script reports its predictions.
- **12 to 15 Oct:** A1 for all six tasks, the frozen harness, the leakage screen, and A4 findings with their evidence. Make the A1-off and A4-off config switches work.
- **16 to 18 Oct:** The C5 policy, and the set of planted-leakage scripts with clean controls.
- **19 to 28 Oct:** Run the leakage stress test and the finding-accuracy check.

### 4. Interaction layer

Everything a human or scripted monitor touches.

- **9 to 11 Oct:** Build a fake run folder of hand-made checkpoints, and a dashboard on top of it showing the tree and the validation-versus-probe chart.
- **12 to 15 Oct:** The function that applies prune, correct and override, including dropping stale actions and logging to `applied.jsonl`. Dashboard buttons that write to the queue.
- **16 to 18 Oct:** The C4 policy and a short protocol for the C6 sessions.
- **19 to 28 Oct:** Run two or three C6 sessions on 19 to 20 Oct and turn the observations into the C4/C5 thresholds.

### Shared work

Analysis and writing are split by role:

| Role | Analysis and report sections |
|---|---|
| 1 | Outcome metrics and cost |
| 2 | Error taxonomy and the annotated trajectories |
| 3 | Validation-test gap, probe fidelity and the reliability checks |
| 4 | Interaction cost and the C6 write-up |

Everyone adds a line to [`contributions.md`](contributions.md) each week.

## Scope cuts

These differ from the proposal and will be stated as such in the report.

- **A2 retrieval:** replaced by a few hand-written model cards per modality. This also removes the A2-off ablation and the prompt-injection red-team test, both already marked optional or droppable.
- **Interventions:** only prune, correct and override are implemented properly. Those are all that C4, C5 and final selection need. Abandon (killing a running script) is skipped.
- **Container sandbox:** start with a subprocess. Move to Docker with no network and a read-only harness only if there is time before the freeze.
- **Dashboard:** tree view and the validation-versus-probe chart. Replay mode only if there is time.

## If we slip further

Follow the proposal's rule: drop tasks before seeds. Going from six tasks to four cuts a third of the compute and keeps five seeds. A4-off is the first condition to lose.

If the walking skeleton is not running by Sunday 11 Oct, cut to four tasks immediately.
