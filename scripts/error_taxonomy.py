"""Error taxonomy: how and why the agent's nodes fail, across saved runs.

Role 2's analysis section. Reads only run folders (the latest complete checkpoint,
config.yaml, and each node's files), so every table can be regenerated from saved runs.

Each node gets one category:

    working              executed and scored
    generation_error     the model returned no script, twice
    leakage              A1's screen rejected the script
    timeout              killed at the time limit
    runtime_error        non-zero exit; `subtype` says which exception (import_error, ...)
    invalid_submission   ran, but predictions.csv was missing or malformed
    pruned / abandoned   stopped by an intervention

Working nodes can also carry labels, which need the whole tree:

    validation_overfitting  beat its parent on validation but did worse on the check
                            score (test once graded, else probe)
    no_gain                 an improve that did not beat its parent by improve_min_rel_gain
    no_change               an improve whose predictions equal its parent's
    unused_data             the script never names one of the input files

Per run: stagnation (the longest stretch of nodes without a new best validation score,
and nodes spent after the final best), debug chains (fixed or not, attempts needed), and
selection regret (how much worse the final pick is on the check score than the best node).

    python scripts/error_taxonomy.py                         # every run under runs/
    python scripts/error_taxonomy.py runs/c1_* --out analysis/taxonomy
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

from imle.controller import beats, latest_complete_checkpoint
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]

# Exception class (last dotted part) -> runtime subtype.
SUBTYPES = {
    "ModuleNotFoundError": "import_error",
    "ImportError": "import_error",
    "KeyError": "missing_key_or_column",
    "IndexError": "index_error",
    "FileNotFoundError": "missing_file",
    "MemoryError": "out_of_memory",
    "TypeError": "type_error",
    "AttributeError": "attribute_error",
    "NameError": "name_error",
    "SyntaxError": "syntax_error",
    "IndentationError": "syntax_error",
    "ZeroDivisionError": "arithmetic_error",
    "PermissionError": "permission_error",
}
_SHAPE = re.compile(r"shape|dimension|features|inconsistent numbers of samples|length", re.IGNORECASE)
_EXCEPTION_LINE = re.compile(r"^([A-Za-z_][\w.]*(?:Error|Exception|Exit|Interrupt))\b:?\s*(.*)$")


def find_runs(paths: list[Path]) -> list[Path]:
    """Run folders among `paths`: each path that has checkpoints/, or its subfolders that do."""
    runs = []
    for path in paths:
        if (path / "checkpoints").is_dir():
            runs.append(path)
        elif path.is_dir():
            runs += sorted(p for p in path.iterdir() if (p / "checkpoints").is_dir())
    return runs


def category(node: Node) -> str:
    """The node's category: working, pruned, abandoned, or the error kind the controller recorded."""
    if node.status == NodeStatus.WORKING:
        return "working"
    if node.status in (NodeStatus.PRUNED, NodeStatus.ABANDONED):
        return node.status.value
    if node.status == NodeStatus.RUNNING:
        return "unfinished"
    return (node.error or "unknown").split(":")[0].strip() or "unknown"


def runtime_subtype(stderr: str) -> tuple[str, str]:
    """(subtype, exception line) for a crashed script, from the last exception line of its stderr."""
    line = ""
    for raw in reversed(stderr.strip().splitlines()):
        if _EXCEPTION_LINE.match(raw.strip()):
            line = raw.strip()
            break
    if not line:
        return "other", ""
    name, message = _EXCEPTION_LINE.match(line).groups()
    name = name.split(".")[-1]
    if name in SUBTYPES:
        return SUBTYPES[name], line[:200]
    if name == "ValueError":
        return ("shape_mismatch" if _SHAPE.search(message) else "value_error"), line[:200]
    return "other", line[:200]


def check_score(node: Node) -> tuple[float | None, str]:
    """The score used to judge real performance: test once graded, else probe."""
    if node.test_score is not None:
        return node.test_score, "test"
    return node.probe_score, "probe"


def worse(tree: Tree, a: float, b: float) -> bool:
    """Whether score `a` is strictly worse than `b` for this task's direction."""
    return a < b if tree.higher_is_better else a > b


def same_predictions(run_dir: Path, a: str, b: str) -> bool:
    """Whether two nodes wrote the same predictions (same ids, values within 1e-9)."""
    paths = [run_dir / "nodes" / n / "output" / "predictions.csv" for n in (a, b)]
    if not all(p.exists() for p in paths):
        return False
    try:
        x, y = (pd.read_csv(p) for p in paths)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError):
        return False
    if list(x.columns) != list(y.columns) or len(x) != len(y):
        return False
    key = x.columns[0]
    x, y = x.sort_values(key).reset_index(drop=True), y.sort_values(key).reset_index(drop=True)
    for col in x.columns:
        if pd.api.types.is_numeric_dtype(x[col]) and pd.api.types.is_numeric_dtype(y[col]):
            if not ((x[col] - y[col]).abs().fillna(0) <= 1e-9).all():
                return False
        elif not x[col].astype(str).equals(y[col].astype(str)):
            return False
    return True


def unused_inputs(run_dir: Path, script: str) -> list[str]:
    """Top-level input files or folders whose name never appears in the script (a text heuristic)."""
    input_dir = run_dir / "workspace" / "input"
    if not input_dir.is_dir():
        return []
    return sorted(p.name for p in input_dir.iterdir() if not p.name.startswith(".") and p.name not in script)


def classify_run(run_dir: Path) -> tuple[list[dict], dict]:
    """One row per node, and one summary row for the run."""
    ck = latest_complete_checkpoint(run_dir)
    if ck is None:
        return [], {}
    tree = Tree.model_validate(ck["tree"])
    status = ck["status"]
    cfg_path = run_dir / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
    min_gain = ((cfg.get("search") or {}).get("improve_min_rel_gain")) or 0.0
    base = {"run": run_dir.name, "condition": status.get("condition"), "task": status.get("task"),
            "seed": status.get("seed")}

    rows = []
    for node in tree.nodes.values():
        parent = tree.nodes.get(node.parent_id) if node.parent_id else None
        cat = category(node)
        node_dir = run_dir / "nodes" / node.id
        row = {**base, "node": node.id, "operator": node.operator.value, "parent": node.parent_id,
               "category": cat, "subtype": "", "exception": "", "val": node.val_score,
               "probe": node.probe_score, "test": node.test_score, "labels": ""}
        if cat == "runtime_error":
            stderr_path = node_dir / "stderr.txt"
            stderr = stderr_path.read_text(errors="replace") if stderr_path.exists() else (node.error or "")
            row["subtype"], row["exception"] = runtime_subtype(stderr)

        labels = []
        if cat == "working" and parent is not None and parent.val_score is not None:
            if node.operator == Operator.IMPROVE:
                if not beats(tree, node.val_score, parent.val_score, min_gain):
                    labels.append("no_gain")
                if same_predictions(run_dir, node.id, parent.id):
                    labels.append("no_change")
            node_check, basis = check_score(node)
            parent_check, parent_basis = check_score(parent)
            if (node_check is not None and parent_check is not None and basis == parent_basis
                    and worse(tree, parent.val_score, node.val_score) and worse(tree, node_check, parent_check)):
                labels.append("validation_overfitting")
        script_path = run_dir / node.script_path if node.script_path else None
        missing = []
        if cat == "working" and script_path and script_path.exists():
            missing = unused_inputs(run_dir, script_path.read_text(errors="replace"))
        if missing:
            labels.append("unused_data:" + "+".join(missing))
        row["labels"] = ",".join(labels)
        rows.append(row)

    return rows, {**base, **run_summary(tree, status)}


def run_summary(tree: Tree, status: dict) -> dict:
    """Stagnation, debug chains and selection regret for one run."""
    nodes = list(tree.nodes.values())
    best, streak, longest, last_best_index = None, 0, 0, -1
    for i, n in enumerate(nodes):
        if n.status == NodeStatus.WORKING and n.val_score is not None and (best is None or worse(tree, best, n.val_score)):
            best, streak, last_best_index = n.val_score, 0, i
        else:
            streak += 1
            longest = max(longest, streak)

    chains: dict[str, list[Node]] = {}
    for n in nodes:
        if n.operator != Operator.DEBUG:
            continue
        root = n
        while root.operator == Operator.DEBUG and root.parent_id:
            root = tree.nodes[root.parent_id]
        chains.setdefault(root.id, []).append(n)
    fixed = [c for c in chains.values() if any(n.status == NodeStatus.WORKING for n in c)]
    attempts_to_fix = [next(i for i, n in enumerate(c, 1) if n.status == NodeStatus.WORKING) for c in fixed]

    working = [n for n in nodes if n.status == NodeStatus.WORKING and n.val_score is not None]
    final = tree.nodes.get(status.get("final_node") or "")
    regret, basis = None, ""
    checked = [(n, *check_score(n)) for n in working]
    if final is not None and checked:
        final_check, basis = check_score(final)
        same_basis = [s for _, s, b in checked if s is not None and b == basis]
        if final_check is not None and same_basis:
            best_check = max(same_basis) if tree.higher_is_better else min(same_basis)
            regret = abs(final_check - best_check)
    return {
        "nodes": len(nodes),
        "working_rate": round(len(working) / len(nodes), 3) if nodes else None,
        "longest_no_new_best": longest,
        "nodes_after_final_best": len(nodes) - 1 - last_best_index if last_best_index >= 0 else len(nodes),
        "failures_debugged": len(chains),
        "debug_chains_fixed": len(fixed),
        "mean_attempts_to_fix": round(sum(attempts_to_fix) / len(attempts_to_fix), 2) if attempts_to_fix else None,
        "final_node": status.get("final_node"),
        "stop_reason": status.get("stop_reason"),
        "done": bool(status.get("done")),
        "selection_regret": round(regret, 4) if regret is not None else None,
        "regret_basis": basis,
    }


def md_table(df: pd.DataFrame) -> str:
    """A pandas frame as a markdown table, without needing the tabulate package."""
    if df.empty:
        return "(none)\n"
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r.tolist()) + " |")
    return "\n".join(lines) + "\n"


def summarise(nodes: pd.DataFrame, runs: pd.DataFrame) -> str:
    """The markdown report: category shares, runtime subtypes, labels, debug and run-level tables."""
    out = [f"# Error taxonomy\n\n{len(runs)} runs, {len(nodes)} nodes.\n"]

    counts = nodes.groupby(["condition", "category"]).size().unstack(fill_value=0)
    shares = (counts.div(counts.sum(axis=1), axis=0) * 100).round(1)
    table = counts.astype(str) + " (" + shares.astype(str) + "%)"
    out += ["## Node categories by condition\n", md_table(table.reset_index())]

    runtime = nodes[nodes.category == "runtime_error"]
    sub = runtime.groupby("subtype").size().sort_values(ascending=False).rename("nodes").reset_index()
    out += ["## Runtime errors by exception\n", md_table(sub)]
    examples = runtime.drop_duplicates("subtype")[["subtype", "run", "node", "exception"]]
    out += ["Example of each:\n", md_table(examples)]

    by_op = nodes.groupby(["operator", "category"]).size().unstack(fill_value=0)
    out += ["## Categories by operator\n", md_table(by_op.reset_index())]

    label_counts = Counter(
        label.split(":")[0] for labels in nodes["labels"] if labels for label in labels.split(",")
    )
    working = int((nodes.category == "working").sum())
    improves = int(((nodes.category == "working") & (nodes.operator == "improve")).sum())
    label_rows = pd.DataFrame(
        [{"label": k, "nodes": v, "of": improves if k in ("no_gain", "no_change") else working}
         for k, v in sorted(label_counts.items())]
    )
    out += ["## Labels on working nodes\n",
            "`no_gain` and `no_change` are out of working improve nodes; the others out of all working nodes.\n",
            md_table(label_rows)]

    run_cols = ["run", "condition", "task", "seed", "nodes", "working_rate", "longest_no_new_best",
                "nodes_after_final_best", "failures_debugged", "debug_chains_fixed", "mean_attempts_to_fix",
                "final_node", "selection_regret", "regret_basis", "stop_reason", "done"]
    out += ["## Runs\n", md_table(runs[run_cols])]
    return "\n".join(out)


def main() -> None:
    """Classify every node of the given runs and write nodes.csv, runs.csv and summary.md."""
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=[ROOT / "runs"],
                        help="run folders, or folders containing them (default: runs/)")
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "_analysis" / "taxonomy")
    args = parser.parse_args()

    node_rows, run_rows = [], []
    for run_dir in find_runs(args.paths):
        rows, summary = classify_run(run_dir)
        if rows:
            node_rows += rows
            run_rows.append(summary)
    if not node_rows:
        raise SystemExit("no run folders with a complete checkpoint found")

    nodes, runs = pd.DataFrame(node_rows), pd.DataFrame(run_rows)
    nodes["condition"] = nodes["condition"].fillna("unknown")
    args.out.mkdir(parents=True, exist_ok=True)
    nodes.to_csv(args.out / "nodes.csv", index=False)
    runs.to_csv(args.out / "runs.csv", index=False)
    report = summarise(nodes, runs)
    (args.out / "summary.md").write_text(report)
    print(report)
    print(f"written to {args.out}")


if __name__ == "__main__":
    main()
