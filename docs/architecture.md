# Architecture

## Processes

Two kinds of process, never merged:

1. **Agent process**: runs the search loop. The only writer to live state.
2. **Monitor processes**: the Streamlit dashboard and scripted policies. Read the checkpoint, append to the queue.

The dashboard can refresh, crash, or be opened on several laptops without affecting a run.

## Components

| ID | Component | Responsibility |
|---|---|---|
| A1 | Evaluation agent | Runs once. Builds train / validation / probe splits and the scoring harness, then freezes it. Screens each candidate script for leakage and unused data before execution. |
| A2 | Retrieval agent | On draft operations, returns model cards (fixed schema) from allowlisted sources. |
| A3 | Coding agent | Draft, debug, improve operators. Outputs a short plan plus a self-contained script. |
| A4 | Reflection agent | At phase boundaries, writes findings with evidence (node IDs and scores). |
| A5 | Tree controller | Selects node and operator, enforces stopping rules, checkpoints, applies interventions. |

## Splits

| Split | Used by | Purpose |
|---|---|---|
| train | A3 scripts | Fitting |
| validation | A5 selection | The score the agent optimises |
| probe | Monitor only | A signal the agent never sees, for detecting drift |
| test | Grading only | Graded per node for analysis; never shown to any agent |

## Permissions

Enforced by the environment (file permissions, network rules), not by prompts.

| | Read data | Write harness | Execute code | Web | Write tree / KB |
|---|---|---|---|---|---|
| A1 | yes | yes, once | sandbox | no | no |
| A2 | no | no | no | allowlist | model cards only |
| A3 | yes | **no** | sandbox | no | no |
| A4 | no | no | no | no | findings only |
| A5 | no | no | no | no | yes |
| Monitor | view | no | no | no | via queue only |

## Main loop

1. A1 builds splits and harness, freezes harness.
2. A5 selects node and operator.
3. A2 supplies model cards (drafts only); KB supplies findings.
4. A3 writes plan and script; A1 screens it.
5. Sandbox executes; harness scores on validation and probe; test submission graded but hidden.
6. A4 records findings if a phase closed.
7. **Safe point**: A5 checkpoints, drains queue, applies interventions.
8. Repeat until budget or node cap. Final submission chosen by configured policy.

## Prompt injection

A2 reads untrusted web pages, and A3's output is executed. Mitigations:

- A2 returns only the model-card schema, never free text.
- Model cards are delimited and labelled untrusted in A3's prompt.
- A2 sources are allowlisted.
- The sandbox has no network, no credentials, and no host access.

Red-team check: plant a page with an embedded instruction and verify it does not reach executed code.
