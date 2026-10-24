# C6: live session protocol

Role 4. C6 sessions are a few runs where a person watches the dashboard and intervenes while thinking aloud. They are qualitative: a source of hypotheses for the scripted policies, not a user study (proposal, Section 4). Each one costs a run's budget (2 hours) of one person's attention.

## Goal of each session

1. See what a person notices on the dashboard and what makes them act.
2. Check the C4 rule against that behaviour: would `divergence_prune` have pruned where the person pruned, and only there?
3. Measure interaction cost: interventions, their timing, and the human time each took.

## Setup

- **Participant:** a group member who has not seen that run before. One participant per session. An observer takes notes; the participant does not touch the terminal.
- **Run:** condition `c6_live.yaml` (monitors: `human`), a 2-hour budget, the same model and evaluator as the C1 runs.
  - Tasks: `spooky-author-identification` and `leaf-classification`. Spooky's probe split is large (about 1,760 rows), so its signal is reliable. Leaf's is small (about 90 rows) and showed validation overfitting in the MiniMax pilot.
  - Seed: 100 and up, so the run never coincides with a C1 seed.
- **Start the run:**

  ```bash
  python scripts/cloud_run.py --config configs/conditions/c6_live.yaml \
      --task spooky-author-identification --seed 100 --budget-hours 2 --evaluator stand_in
  streamlit run dashboard/app.py
  ```

- **Dashboard:** Live view, test scores off (the toggle is disabled until the run finishes). Start the session (open the page) after the agent's drafts are done, about 10 to 20 minutes in, so there is something to look at.

## During the session

**Brief the participant (read aloud):**

> The agent searches for a good model. Each point is one attempt. Blue is the score it optimises (validation); orange is a held-out probe the agent never sees. You can prune a branch, choose the final submission, steer the next attempt, add an idea, or fix one of its notes. Changes apply after the current attempt finishes. Please say what you are looking at and why, as you go. You do not have to intervene.

**Rules:**

- The participant acts only through the dashboard.
- The observer only prompts for speech ("what are you looking at?") and does not suggest actions.
- Breaks are fine. The run does not pause (`intervention-protocol.md`, rule 5).

**The observer's notes,** one line per moment, in `runs/<run>/c6_notes.md`:

| Time | Node on screen | What they said | What they did |
|---|---|---|---|
| 14:05 | n31 | "validation keeps going down but orange is flat" | none yet |

**Recorded automatically:**

- `queue.jsonl`: every intervention, with the reason typed in the form.
- `applied.jsonl`: whether each one applied, or why it was dropped.
- `dashboard_log.jsonl`: session start, nodes looked at, and interventions queued, with timestamps.

## After the session

1. **Debrief (5 minutes):**
   - What made you intervene?
   - What did you ignore on purpose?
   - What would you have wanted to see?
2. **Post-hoc C2 and C3, once the run finishes:**

   ```bash
   python scripts/grade.py runs/C6_<task>_seed100
   python scripts/outcomes.py runs/C6_<task>_seed100
   ```

3. **Compare the participant with the C4 rule:**

   ```bash
   python scripts/replay_policy.py runs/C6_<task>_seed100
   ```

   The replay applies the participant's prunes as they happened (they are in the checkpoints) and lists where `divergence_prune` would have pruned. Fill in the agreement table:

   | | C4 prunes | C4 does not prune |
   |---|---|---|
   | **Person prunes** | agree | the rule misses this cue |
   | **Person does not prune** | the rule fires on noise | agree |

4. **Interaction cost:**

   ```bash
   python scripts/interaction_cost.py runs/C6_*
   ```

## Turning observations into the C4 and C5 thresholds

C4's thresholds (`policies.divergence_prune` in `configs/base.yaml`) were set before any session, from the C1 pilots. They are:

- at least 2 working nodes since the lineage's best-probe node;
- a 1% validation gain and a 1% probe loss since that node;
- a probe loss that holds in 95% of paired bootstrap resamples.

After the sessions:

- If people pruned **earlier** than the rule (after one node, or on a flat probe rather than a falling one), lower `min_steps` or `min_probe_loss`.
- If they **ignored** divergences the rule acts on, raise them.

Freeze the thresholds before the C4 runs start: changing them halfway splits C4 into two conditions. Hand C5 cues (findings people corrected and why) to role 3.

## Write-up (report)

- **Interaction cost table:** from `interaction_cost.py`.
- **Agreement table:** person vs C4 rule, per session.
- **Cues people used, quoted:** two or three, from `c6_notes.md`.
- **One annotated trajectory per session:**

  ```bash
  python scripts/trajectory.py runs/C6_<task>_seed100
  ```

- **Limitations:** few sessions; participants from the group, who know how the agent works; one model.
