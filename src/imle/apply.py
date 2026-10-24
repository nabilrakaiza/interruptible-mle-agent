"""Applying queued interventions at a safe point.

Owned by role 4 (docs/plan.md). Written first as role 2's stand-in, and kept as
role 4's implementation after review; `apply_pending`'s signature is what the
controller calls.

Rules, from docs/intervention-protocol.md: drain the queue in timestamp order,
validate each action against the current state, drop it when the target is
missing or in the wrong state, and record every outcome in applied.jsonl.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from imle.intervention import Action, AppliedRecord, Intervention, pending
from imle.state import SearchState
from imle.tree import NodeStatus, Operator, Tree

# A handler returns None when it applied the action, or the reason it was dropped.
Handler = Callable[[Intervention, Tree, list, SearchState], "str | None"]


def apply_pending(run_dir: Path, tree: Tree, findings: list[dict[str, Any]], state: SearchState) -> list[AppliedRecord]:
    """Apply or drop every queued intervention not yet handled, and log each to applied.jsonl.

    Changes `tree`, `findings` and `state` in place. Returns the records written.
    """
    applied_path = run_dir / "applied.jsonl"
    try:
        items = pending(run_dir / "queue.jsonl", applied_path)
    except ValueError as e:  # a malformed queue line must not crash the run
        print(f"warning: queue.jsonl could not be read, no interventions applied: {e}")
        return []

    records = []
    for item in items:
        try:
            reason = HANDLERS[item.action](item, tree, findings, state)
        except (KeyError, TypeError, ValueError) as e:
            reason = f"invalid params: {e}"
        record = AppliedRecord(
            intervention=item,
            outcome="applied" if reason is None else "dropped",
            reason=reason,
            applied_at=datetime.now(timezone.utc).isoformat(),
        )
        with applied_path.open("a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        records.append(record)
    return records


def _prune(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Exclude a node and its whole subtree from selection."""
    node = tree.nodes.get(item.target or "")
    if node is None:
        return f"unknown node {item.target}"
    if node.status == NodeStatus.PRUNED:
        return "already pruned"
    removed = set(tree.subtree_ids(node.id))
    for node_id in removed:
        tree.nodes[node_id].status = NodeStatus.PRUNED
    if state.forced_next and state.forced_next.get("parent_id") in removed:
        state.forced_next = None
    if state.override_node in removed:
        state.override_node = None
    return None


def _redirect(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Force the next selection: `params.operator` applied to the target node."""
    operator = Operator(item.params["operator"])
    if operator == Operator.DRAFT:
        state.forced_next = {"operator": operator.value, "parent_id": None}
        return None
    node = tree.nodes.get(item.target or "")
    if node is None:
        return f"unknown node {item.target}"
    if operator == Operator.DEBUG and (node.status != NodeStatus.BUGGY or not node.script_path):
        return f"debug needs a buggy node with a script, {node.id} is {node.status.value}"
    if operator == Operator.IMPROVE and node.status != NodeStatus.WORKING:
        return f"improve needs a working node, {node.id} is {node.status.value}"
    state.forced_next = {"operator": operator.value, "parent_id": node.id}
    return None


def _override(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Use the target node as the final submission, whatever the selection mode."""
    node = tree.nodes.get(item.target or "")
    if node is None:
        return f"unknown node {item.target}"
    if node.status != NodeStatus.WORKING:
        return f"override needs a working node, {node.id} is {node.status.value}"
    state.override_node = node.id
    return None


def _inject(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Add a model card or approach to the knowledge base. Text becomes a card's summary."""
    card = item.params.get("card")
    if not card:
        return "params.card is missing"
    if isinstance(card, str):
        card = {"name": "injected approach", "summary": card}
    if not isinstance(card, dict):
        return "params.card must be text or an object"
    state.injected_cards.append({**card, "source": item.source})
    return None


def _correct(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Delete a finding, or replace its text when `params.replacement` is given."""
    index = next((i for i, f in enumerate(findings) if f.get("id") == item.target), None)
    if index is None:
        return f"unknown finding {item.target}"
    replacement = item.params.get("replacement")
    if replacement:
        findings[index] = {**findings[index], "text": str(replacement), "corrected_by": item.id}
    else:
        del findings[index]
    return None


def _rebudget(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Add `params.seconds` (which may be negative) to the run's wall-clock budget."""
    state.extra_budget_s += float(item.params["seconds"])
    return None


def _abandon(item: Intervention, tree: Tree, findings: list, state: SearchState) -> str | None:
    """Always dropped: abandon is cut from scope, and nothing runs at a safe point anyway."""
    return "abandon is not supported (scope cut in docs/plan.md)"


HANDLERS: dict[Action, Handler] = {
    Action.PRUNE: _prune,
    Action.REDIRECT: _redirect,
    Action.OVERRIDE: _override,
    Action.INJECT: _inject,
    Action.CORRECT: _correct,
    Action.REBUDGET: _rebudget,
    Action.ABANDON: _abandon,
}
