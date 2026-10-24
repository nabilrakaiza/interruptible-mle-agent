"""Finding accuracy: what fraction of A4's findings are not supported by the nodes they cite.

Role 3's reliability check (docs/experiments.md). Reads only checkpoints, through
imle.checkpoint. Every finding that appeared in any checkpoint of a run is checked
once, against the tree of the first checkpoint that contains it (the tree A4 saw;
later prunes are C5's business, not an A4 error).

A finding is SUPPORTED when all of these hold:

    1. it cites at least one node, and every cited node exists in that tree;
    2. every cited validation score equals the node's validation score in the tree
       (within 1e-9; both missing also matches);
    3. its effect holds for every cited node, comparing the node with its baseline:
       the parent's validation score, or for a node without a scored parent the median
       validation score of the other working drafts (no such baseline: not supported).
       Gains are measured in the metric's better direction.
           helps    the node is working and strictly better than its baseline
           hurts    the node is buggy, or working and strictly worse than its baseline
           neutral  no score check

A finding is REPLICATED when it is supported and condition 3 also holds with probe
scores in place of validation scores (buggy nodes count as they do for validation).
The probe is the split A4 never sees, so this is the stricter test.

    python scripts/finding_accuracy.py runs/c1_*            # one or more run folders
    python scripts/finding_accuracy.py runs/* --out results/finding_accuracy.csv

Writes one row per finding to --out and one row per run to the same name with _runs.
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

import pandas as pd

from imle import checkpoint
from imle.tree import Node, NodeStatus, Tree

TOLERANCE = 1e-9


def first_appearances(run_dir: Path) -> list[tuple[dict, Tree, int]]:
    """(finding, tree, step) for each finding ID, at the first complete checkpoint that holds it."""
    root = run_dir / "checkpoints"
    steps = sorted(int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit()) if root.exists() else []
    seen, out = set(), []
    for step in steps:
        ck = checkpoint.read(run_dir, step)
        if ck is None:
            continue
        tree = None
        for f in ck["findings"]:
            if f.get("id") in seen:
                continue
            seen.add(f.get("id"))
            tree = tree or Tree.model_validate(ck["tree"])
            out.append((f, tree, step))
    return out


def baseline(tree: Tree, node: Node, field: str) -> float | None:
    """The score `node` is compared with: its parent's, else the median of the other working drafts."""
    parent = tree.nodes.get(node.parent_id) if node.parent_id else None
    if parent is not None:
        return getattr(parent, field)
    others = [getattr(n, field) for n in tree.nodes.values() if n.parent_id is None and n.id != node.id
              and n.status == NodeStatus.WORKING and getattr(n, field) is not None]
    return statistics.median(others) if others else None


def effect_holds(tree: Tree, node: Node, effect: str, field: str) -> tuple[bool, str]:
    """Whether the node shows `effect` on `field` (val_score or probe_score), and why not."""
    if effect == "neutral":
        return True, ""
    if effect == "hurts" and node.status == NodeStatus.BUGGY:
        return True, ""
    score, base = getattr(node, field), baseline(tree, node, field)
    if node.status != NodeStatus.WORKING or score is None:
        return False, f"{node.id} is {node.status.value} with no {field}"
    if base is None:
        return False, f"{node.id} has no baseline to compare {field} with"
    gain = (score - base) if tree.higher_is_better else (base - score)
    if effect == "helps" and gain > 0 or effect == "hurts" and gain < 0:
        return True, ""
    return False, f"{node.id} {field} gain {gain:+.4g} does not show '{effect}'"


def check(finding: dict, tree: Tree) -> dict:
    """supported, replicated and the first reason each failed."""
    evidence = [e for e in finding.get("evidence", []) if isinstance(e, dict)]
    effect = str(finding.get("effect", "neutral"))
    reason = ""
    if not evidence:
        reason = "cites no nodes"
    for e in evidence:
        node = tree.nodes.get(e.get("node_id"))
        if node is None:
            reason = reason or f"cited node {e.get('node_id')} missing"
            continue
        cited, actual = e.get("val_score"), node.val_score
        if (cited is None) != (actual is None) or (cited is not None and abs(cited - actual) > TOLERANCE):
            reason = reason or f"{node.id} cited val {cited}, tree has {actual}"
            continue
        ok, why = effect_holds(tree, node, effect, "val_score")
        if not ok:
            reason = reason or why
    supported = not reason
    probe_reason = ""
    if supported:
        for e in evidence:
            ok, why = effect_holds(tree, tree.nodes[e["node_id"]], effect, "probe_score")
            if not ok:
                probe_reason = probe_reason or why
    return {"supported": supported, "reason": reason, "replicated": supported and not probe_reason,
            "probe_reason": probe_reason}


def analyse(run_dirs: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-finding and per-run tables."""
    rows = []
    for run_dir in run_dirs:
        for finding, tree, step in first_appearances(run_dir):
            rows.append({"run": run_dir.name, "finding_id": finding.get("id"), "step": step,
                         "effect": finding.get("effect", "neutral"), "n_cited": len(finding.get("evidence", [])),
                         "text": finding.get("text", ""), **check(finding, tree)})
    findings = pd.DataFrame(rows, columns=["run", "finding_id", "step", "effect", "n_cited", "text", "supported",
                                           "reason", "replicated", "probe_reason"])
    runs = (findings.groupby("run", sort=True)
            .agg(findings=("finding_id", "size"), unsupported_fraction=("supported", lambda s: 1 - s.mean()),
                 replicated_fraction=("replicated", "mean"))
            .reset_index()) if len(findings) else pd.DataFrame(
        columns=["run", "findings", "unsupported_fraction", "replicated_fraction"])
    return findings, runs


def main(argv: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+", type=Path, help="run folders")
    parser.add_argument("--out", type=Path, default=Path("results/finding_accuracy.csv"))
    args = parser.parse_args(argv)
    findings, runs = analyse([p for p in args.runs if p.is_dir()])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    findings.to_csv(args.out, index=False)
    runs.to_csv(args.out.with_name(args.out.stem + "_runs.csv"), index=False)
    print(runs.to_string(index=False) if len(runs) else "no findings in these runs")
    if len(findings):
        print(f"overall: {len(findings)} findings, {1 - findings['supported'].mean():.1%} unsupported, "
              f"{findings['replicated'].mean():.1%} replicated on probe")
    print(f"wrote {args.out}")
    return findings, runs


if __name__ == "__main__":
    main()
