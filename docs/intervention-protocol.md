# Intervention protocol

This is the contract between the agent and every monitor (dashboard and scripted policies). Change it only by pull request.

## Safe points

A safe point is a node boundary: after a script has executed and been scored and written to the tree, and before A5 selects the next node. It is the only moment when all state is consistent. Interventions apply only here.

Running scripts are not interrupted, except by the optional `abandon` action.

## Checkpoint layout

Written by the agent at every safe point. Every checkpoint is kept, which enables replay.

```
runs/<run_id>/
  config.yaml
  checkpoints/
    000042/
      tree.json
      findings.json
      status.json        # current node, elapsed budget, timestamp
  queue.jsonl            # appended by monitors
  applied.jsonl          # written by agent: applied and dropped actions
  llm_calls.jsonl        # every prompt, completion, model, tokens
```

Writes are atomic: write `file.tmp`, then rename. Readers never see a half-written file.

## Queue format

`queue.jsonl`, one JSON object per line, append only.

```json
{"id": "q-0007", "ts": "2026-10-20T14:03:11Z", "source": "human", "action": "prune", "target": "n17", "note": "val up, probe flat"}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique ID for this request |
| `ts` | yes | UTC timestamp |
| `source` | yes | `human` or a policy name such as `c4_divergence_prune` |
| `action` | yes | One of the actions below |
| `target` | depends | Node ID or finding ID |
| `params` | no | Action-specific parameters |
| `note` | no | Free text reason, kept for analysis |

## Actions

| Action | Type | Target | Effect |
|---|---|---|---|
| `prune` | action | node | Exclude node and its subtree from selection |
| `redirect` | action | node | Force next selection; `params.operator` in {draft, debug, improve} |
| `override` | action | node | Use this node as the final submission |
| `inject` | belief | none | Add a model card or approach; `params.card` |
| `correct` | belief | finding | Delete or replace a finding; `params.replacement` optional |
| `rebudget` | budget | none | `params.seconds` added (may be negative) |
| `abandon` | budget | running node | Terminate the running script; node marked abandoned |

## Application rules

1. Drain the queue in timestamp order at each safe point.
2. Validate each action against current state. If the target is missing or in the wrong state, **drop** it.
3. Record every applied or dropped action in `applied.jsonl` with the reason.
4. Abandoned nodes get no score. Partial scores are not comparable and would corrupt selection.
5. The budget clock does not pause while waiting on a human.

## Why scripted policies use the same queue

Human and scripted interventions pass through identical code, so comparing them is fair by construction.
