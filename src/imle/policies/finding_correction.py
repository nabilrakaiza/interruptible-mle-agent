"""C5: scripted belief intervention.

Reads the latest checkpoint. When later nodes contradict a finding's evidence,
appends a `correct` action deleting that finding.

The controller calls `decide(run_dir, ck)` at every safe point (the monitor
interface in docs/core-agent-assumptions.md, the same one C4's divergence_prune
uses) and appends what it returns to queue.jsonl, adding `id`, `ts` and `source`.
The deletion then goes through apply_pending like a human's.

Each node a finding cites is checked against the current tree:

    failed     missing from the tree, pruned or abandoned; buggy, unless the finding
               says the change hurts (a crash is then the evidence); or it does not
               replicate on the probe: compared with its parent, with gains measured
               in the metric's better direction,
                   helps:  validation gain - probe gain > max_gap
                   hurts:  probe gain - validation gain > max_gap
    passed     scored, with a scored parent, and none of the above
    unchecked  no parent, or scores missing (only the status checks apply)

A finding is deleted when at least `min_fail_fraction` of its checked nodes failed.
Neutral findings get the status checks only. A finding already targeted by a
`correct` in queue.jsonl or applied.jsonl is skipped, so a rerun or a second
checkpoint at the same safe point never asks twice.

Thresholds: keyword arguments, else `finding_correction:` in the run's config.yaml
(configs/conditions/c5_finding_correction.yaml), else the defaults below.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from imle import intervention
from imle.intervention import Action
from imle.tree import Node, NodeStatus, Tree

MAX_GAP = 0.02
MIN_FAIL_FRACTION = 0.5


def thresholds(run_dir: Path, max_gap: float | None = None, min_fail_fraction: float | None = None) -> dict:
    """The thresholds in force: arguments first, then the run's config, then the defaults."""
    path = run_dir / "config.yaml"
    cfg = ((yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}).get(
        "finding_correction") or {}
    return {"max_gap": float(max_gap if max_gap is not None else cfg.get("max_gap", MAX_GAP)),
            "min_fail_fraction": float(min_fail_fraction if min_fail_fraction is not None
                                       else cfg.get("min_fail_fraction", MIN_FAIL_FRACTION))}


def already_targeted(run_dir: Path) -> set[str]:
    """Finding IDs that a `correct` in the queue or the applied log already targets."""
    targets = {i.target for i in intervention.read_all(run_dir / "queue.jsonl") if i.action == Action.CORRECT}
    applied = run_dir / "applied.jsonl"
    if applied.exists():
        for line in applied.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)["intervention"]
                if item.get("action") == Action.CORRECT.value:
                    targets.add(item.get("target"))
    return {t for t in targets if t}


def check_node(tree: Tree, node_id: str, effect: str, max_gap: float) -> tuple[str, str]:
    """("failed" | "passed" | "unchecked", why) for one cited node."""
    node: Node | None = tree.nodes.get(node_id)
    if node is None:
        return "failed", f"{node_id} missing"
    if node.status in (NodeStatus.PRUNED, NodeStatus.ABANDONED):
        return "failed", f"{node_id} {node.status.value}"
    if node.status == NodeStatus.BUGGY:
        return ("passed", f"{node_id} buggy") if effect == "hurts" else ("failed", f"{node_id} buggy")
    parent = tree.nodes.get(node.parent_id) if node.parent_id else None
    scores = [node.val_score, node.probe_score, parent.val_score if parent else None,
              parent.probe_score if parent else None]
    if effect == "neutral" or any(s is None for s in scores):
        return "unchecked", f"{node_id} not comparable"
    sign = 1 if tree.higher_is_better else -1
    val_gain = sign * (node.val_score - parent.val_score)
    probe_gain = sign * (node.probe_score - parent.probe_score)
    gap = val_gain - probe_gain if effect == "helps" else probe_gain - val_gain
    why = f"{node_id} val {val_gain:+.4g}, probe {probe_gain:+.4g} vs {parent.id}"
    return ("failed" if gap > max_gap else "passed"), why


def decide(run_dir: Path, ck: dict | None, *, max_gap: float | None = None,
           min_fail_fraction: float | None = None) -> list[dict[str, Any]]:
    """`correct` interventions deleting each finding whose cited nodes failed to replicate."""
    if not ck or not ck.get("findings"):
        return []
    run_dir = Path(run_dir)
    limits = thresholds(run_dir, max_gap, min_fail_fraction)
    tree = Tree.model_validate(ck["tree"])
    skip = already_targeted(run_dir)
    out = []
    for finding in ck["findings"]:
        fid = finding.get("id")
        if not fid or fid in skip:
            continue
        effect = str(finding.get("effect", "neutral"))
        results = [check_node(tree, e["node_id"], effect, limits["max_gap"])
                   for e in finding.get("evidence", []) if isinstance(e, dict) and e.get("node_id")]
        checked = [r for r in results if r[0] != "unchecked"]
        failed = [why for outcome, why in checked if outcome == "failed"]
        if checked and len(failed) / len(checked) >= limits["min_fail_fraction"]:
            out.append({"action": Action.CORRECT.value, "target": fid,
                        "note": f"C5: {len(failed)} of {len(checked)} cited nodes failed to replicate: "
                                + "; ".join(failed)})
            skip.add(fid)
    return out
