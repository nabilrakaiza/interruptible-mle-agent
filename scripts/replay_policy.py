"""Replay a scripted policy over saved runs: where it would have intervened, and what that would change.

Feeds every saved checkpoint of a finished run, in order, to `imle.policies.<name>.decide`,
exactly as the controller does at each safe point. A prune it asks for is applied to the
replayed tree, so later checkpoints see that subtree as pruned. Nothing in the run folder
is changed.

This is a post-hoc estimate, not a C4 run: in a real run the agent would have searched
elsewhere after a prune, and those nodes do not exist here. It is used to

    - set the policy's thresholds from C1 runs before the C4 runs start,
    - check that the policy fires where a person looking at the dashboard would, and
    - report a post-hoc "C4 applied to C1" final pick next to C1's own (like C2 and C3).

Test scores are read only for the last of these, and are never passed to the policy.

    python scripts/replay_policy.py runs/minimax/*                        # divergence_prune
    python scripts/replay_policy.py runs/* --set min_steps=3 --set min_val_gain=0.02
    python scripts/replay_policy.py runs/* --out analysis/replay          # also writes CSVs
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from imle import checkpoint
from imle.controller import ranked
from imle.tree import NodeStatus, Tree


def parse_overrides(pairs: list[str]) -> dict[str, Any]:
    """`key=value` strings as a dict, with each value parsed as YAML (so numbers stay numbers)."""
    out = {}
    for pair in pairs:
        key, _, value = pair.partition("=")
        out[key.strip()] = yaml.safe_load(value)
    return out


def is_run(path: Path) -> bool:
    """Whether a folder is a run folder (it has checkpoints)."""
    return (path / "checkpoints").is_dir()


def find_runs(paths: list[Path]) -> list[Path]:
    """Run folders among `paths`, looking one and two levels down for folders that hold runs."""
    runs = []
    for p in paths:
        if is_run(p):
            runs.append(p)
        elif p.is_dir():
            runs.extend(sorted(q for q in p.glob("*") if is_run(q)) or sorted(q for q in p.glob("*/*") if is_run(q)))
    return runs


def replay(run_dir: Path, module, overrides: dict[str, Any]) -> tuple[list[dict], list[str]]:
    """The interventions the policy would have queued over the run, in order, and the roots of what it pruned.

    A prune is applied to the replayed tree right away, as apply_pending would at the same
    safe point. Nodes later added below a pruned node would not exist in a real run, so the
    policy is not asked about them and they count as pruned. Checkpoints written after an
    applied intervention repeat the same node and are skipped, as the controller runs
    policies only on the first checkpoint of a safe point.
    """
    original = getattr(module, "settings", None)
    if original is not None:
        module.settings = lambda rd: {**original(rd), **overrides}
    try:
        steps = sorted(int(p.name) for p in (run_dir / "checkpoints").iterdir() if p.name.isdigit())
        roots: list[str] = []
        seen_node = None
        events = []
        for step in steps:
            ck = checkpoint.read(run_dir, step)
            if ck is None:
                continue
            node = ck["status"].get("current_node")
            excluded = pruned_ids(Tree.model_validate(ck["tree"]), roots)
            if node is None or node == seen_node or node in excluded:
                continue
            seen_node = node
            for nid in excluded:
                ck["tree"]["nodes"][nid]["status"] = NodeStatus.PRUNED.value
            for item in module.decide(run_dir, ck):
                removed = 0
                if item.get("action") == "prune" and item.get("target") in ck["tree"]["nodes"]:
                    roots.append(item["target"])
                    removed = len(pruned_ids(Tree.model_validate(ck["tree"]), [item["target"]]) - excluded)
                events.append({"run": run_dir.name, "step": step, "after_node": node, **item,
                               "nodes_removed": removed})
    finally:
        if original is not None:
            module.settings = original
    return events, roots


def pruned_ids(tree: Tree, roots: list[str]) -> set[str]:
    """Every node of `tree` in the subtree of one of `roots`."""
    return {nid for root in roots if root in tree.nodes for nid in tree.subtree_ids(root)}


def final_pick(tree: Tree, excluded: set[str]) -> dict[str, Any]:
    """The best-val node once `excluded` nodes are pruned, with its scores (test for analysis only)."""
    for node in ranked(tree):
        if node.id not in excluded:
            return {"node": node.id, "val": node.val_score, "probe": node.probe_score, "test": node.test_score}
    return {"node": None, "val": None, "probe": None, "test": None}


def summarise(run_dir: Path, events: list[dict], roots: list[str]) -> dict[str, Any]:
    """One row per run: how often the policy fired, and the final pick with and without its prunes.

    `nodes_pruned` counts the pruned subtrees in the finished C1 tree, so it includes nodes
    the agent made there after the prune, which a real run would have spent elsewhere.
    """
    ck = checkpoint.read(run_dir)
    tree = Tree.model_validate(ck["tree"])
    pruned = pruned_ids(tree, roots)
    c1, policy = final_pick(tree, set()), final_pick(tree, pruned)
    return {
        "run": run_dir.name,
        "nodes": len(tree.nodes),
        "interventions": len(events),
        "first_at_node": events[0]["after_node"] if events else None,
        "nodes_pruned": len(pruned),
        "c1_pick": c1["node"], "c1_test": c1["test"],
        "policy_pick": policy["node"], "policy_test": policy["test"],
        "higher_is_better": tree.higher_is_better,
    }


def main() -> None:
    """Command-line entry point: replay a policy over the given runs and print what it would have done."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path, help="run folders, or folders holding them")
    parser.add_argument("--policy", default="divergence_prune", help="module name under imle.policies")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="override one of the policy's thresholds (repeatable)")
    parser.add_argument("--out", type=Path, help="also write interventions.csv and runs.csv here")
    args = parser.parse_args()

    module = importlib.import_module(f"imle.policies.{args.policy}")
    overrides = parse_overrides(args.set)
    all_events, rows = [], []
    for run_dir in find_runs(args.runs):
        events, roots = replay(run_dir, module, overrides)
        all_events.extend(events)
        rows.append(summarise(run_dir, events, roots))
        print(f"{run_dir}: {len(events)} intervention(s)")
        for e in events:
            print(f"  after {e['after_node']}: {e['action']} {e.get('target') or ''} "
                  f"({e['nodes_removed']} nodes) - {e.get('note') or ''}")

    runs = pd.DataFrame(rows)
    if not runs.empty:
        print()
        print(runs.drop(columns=["higher_is_better"]).to_string(index=False))
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(all_events).to_csv(args.out / "interventions.csv", index=False)
        runs.to_csv(args.out / "runs.csv", index=False)
        print(f"\nwrote {args.out}/interventions.csv and runs.csv")


if __name__ == "__main__":
    main()
