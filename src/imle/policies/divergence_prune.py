"""C4: scripted action intervention.

Reads the latest checkpoint. When a subtree's validation gains are not matched
on the probe split, appends a `prune` action to the queue. Uses the same queue
as the dashboard, so human and scripted interventions share one code path.

The rule, checked at every safe point for the node that just finished (`d`):

    1. Walk up d's lineage over working nodes and take the one with the best probe
       score as the anchor `a`: the last point where the lineage was best on data the
       agent never sees.
    2. Prune when, from a to d,
         - at least `min_steps` working nodes came after a (one bad node is not a trend),
         - validation improved by at least `min_val_gain`, relative to a's,
         - probe got worse by at least `min_probe_loss`, relative to a's, and
         - with the stand-in evaluator's labels, d is worse than a on the probe rows in
           at least `consistent_share` of paired bootstrap resamples (a few hundred probe
           rows are noisy; without labels this check is skipped).
    3. The pruned subtree starts at a's child on the path to d, so a itself stays
       selectable and the search can try again from it.

The anchor is working and outside the pruned subtree, so a prune never leaves the run
with nothing to submit.
Thresholds come from `policies.divergence_prune` in the run's config.yaml. The policy
reads `val_score` and `probe_score` only, never `test_score`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from imle import stand_in_evaluation
from imle.tree import Node, NodeStatus, Tree

DEFAULTS = {
    "min_steps": 2,
    "min_val_gain": 0.01,
    "min_probe_loss": 0.01,
    "consistent_share": 0.95,
    "bootstrap_samples": 1000,
}


def settings(run_dir: Path) -> dict[str, Any]:
    """The thresholds: DEFAULTS overridden by `policies.divergence_prune` in the run's config.yaml."""
    path = run_dir / "config.yaml"
    cfg = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}
    return {**DEFAULTS, **((cfg.get("policies") or {}).get("divergence_prune") or {})}


def rel_gain(old: float, new: float, higher_is_better: bool) -> float:
    """How much better `new` is than `old`, relative to |old| (negative when worse)."""
    gain = (new - old) if higher_is_better else (old - new)
    return gain / max(abs(old), 1e-12)


def scored(node: Node | None) -> bool:
    """Whether a node is working and has both a validation and a probe score."""
    return node is not None and node.status == NodeStatus.WORKING and None not in (node.val_score, node.probe_score)


def working_ancestors(tree: Tree, node: Node) -> list[Node]:
    """The scored working nodes above `node` in its lineage, nearest first (buggy ones are skipped)."""
    out = []
    parent = tree.nodes.get(node.parent_id or "")
    while parent is not None:
        if scored(parent):
            out.append(parent)
        parent = tree.nodes.get(parent.parent_id or "")
    return out


def child_towards(tree: Tree, ancestor_id: str, node: Node) -> Node:
    """The child of `ancestor_id` on the path down to `node`."""
    while node.parent_id != ancestor_id:
        node = tree.nodes[node.parent_id]
    return node


def check(run_dir: Path, tree: Tree, node_id: str | None, cfg: dict[str, Any]) -> dict[str, Any] | None:
    """The prune the rule asks for after `node_id` finished, as a queue entry, or None.

    Split out from decide() so replay tools can run the rule over saved trees.
    """
    d = tree.nodes.get(node_id or "")
    if not scored(d):
        return None
    lineage = working_ancestors(tree, d)
    if not lineage:
        return None
    hib = tree.higher_is_better
    anchor = max(lineage, key=lambda n: n.probe_score if hib else -n.probe_score)
    steps = lineage.index(anchor) + 1
    val_gain = rel_gain(anchor.val_score, d.val_score, hib)
    probe_loss = -rel_gain(anchor.probe_score, d.probe_score, hib)
    if steps < cfg["min_steps"] or val_gain < cfg["min_val_gain"] or probe_loss < cfg["min_probe_loss"]:
        return None
    share = stand_in_evaluation.paired_worse_share(run_dir, d.id, anchor.id, "probe", hib,
                                                   int(cfg["bootstrap_samples"]))
    if share is not None and share < cfg["consistent_share"]:
        return None
    target = child_towards(tree, anchor.id, d)
    return {
        "action": "prune",
        "target": target.id,
        "params": {"anchor": anchor.id, "node": d.id, "steps": steps, "val_gain": round(val_gain, 5),
                   "probe_loss": round(probe_loss, 5), "consistent_share": share},
        "note": (f"since {anchor.id}, validation {val_gain:+.1%} but probe {-probe_loss:+.1%} "
                 f"over {steps} nodes, ending at {d.id}"),
    }


def decide(run_dir: Path, ck: dict) -> list[dict]:
    """The controller's hook: at most one prune for the node that just finished."""
    tree = Tree.model_validate(ck["tree"])
    item = check(run_dir, tree, ck["status"].get("current_node"), settings(run_dir))
    return [item] if item else []
