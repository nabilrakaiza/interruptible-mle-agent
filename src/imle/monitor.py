"""Read-only views of a run folder, for the dashboard and the interaction-cost analysis.

Everything here reads checkpoints, queue.jsonl and applied.jsonl, and writes only to
queue.jsonl (through intervention.append) and dashboard_log.jsonl. Nothing touches the
agent's live state, so the dashboard can crash or be open on several laptops at once.

dashboard_log.jsonl records what a person did in the dashboard (session start, nodes
looked at, interventions queued), so C6's human time per intervention can be measured.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from imle import checkpoint
from imle.intervention import Action, Intervention, append, read_all

LOG_NAME = "dashboard_log.jsonl"
STATUS_COLOURS = {"working": "#2e7d32", "buggy": "#c62828", "pruned": "#9e9e9e", "running": "#1565c0",
                  "abandoned": "#6d4c41"}


def now() -> str:
    """The current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def find_runs(root: Path, depth: int = 3) -> list[Path]:
    """Run folders (those with a checkpoints/ folder) under `root`, up to `depth` levels down, sorted."""
    found = []

    def walk(folder: Path, level: int) -> None:
        """Collect run folders below `folder`."""
        if (folder / "checkpoints").is_dir():
            found.append(folder)
            return
        if level >= depth:
            return
        for child in sorted(folder.iterdir()):
            if child.is_dir() and not child.name.startswith((".", "_")):
                walk(child, level + 1)

    if root.is_dir():
        walk(root, 0)
    return sorted(found)


def last_update(run_dir: Path) -> float:
    """When the run last wrote a checkpoint (modification time of its newest checkpoint folder), 0 if none."""
    steps = complete_steps(run_dir)
    return (run_dir / "checkpoints" / f"{steps[-1]:06d}").stat().st_mtime if steps else 0.0


def score_range(points: pd.Series, lines: pd.Series, pad: float = 0.05) -> list[float] | None:
    """A y-axis range that keeps the best-so-far lines and the middle 96% of nodes, so a few wild scores
    (a broken node with log loss 30) do not flatten the chart. None when there is nothing to plot."""
    values = pd.concat([points.quantile([0.02, 0.98]), lines]).dropna()
    if values.empty:
        return None
    lo, hi = float(values.min()), float(values.max())
    margin = (hi - lo) * pad or abs(hi) * pad or 1.0
    return [lo - margin, hi + margin]


def complete_steps(run_dir: Path) -> list[int]:
    """Steps of every fully written checkpoint (status.json present), oldest first."""
    root = run_dir / "checkpoints"
    if not root.is_dir():
        return []
    return sorted(int(p.name) for p in root.iterdir() if p.name.isdigit() and (p / "status.json").exists())


def node_frame(ck: dict, show_test: bool = False) -> pd.DataFrame:
    """One row per node in creation order, with `order` (0, 1, ...) for plotting.

    `test_score` is dropped unless `show_test`: no monitor may see it during a run.
    """
    rows = list(ck["tree"].get("nodes", {}).values())
    cols = ["id", "parent_id", "operator", "status", "val_score", "probe_score", "test_score", "plan", "error",
            "script_path", "started_at", "finished_at"]
    df = pd.DataFrame(rows, columns=cols)
    df.insert(0, "order", range(len(df)))
    if not show_test:
        df = df.drop(columns=["test_score"])
    return df


def best_so_far(nodes: pd.DataFrame, higher_is_better: bool) -> pd.DataFrame:
    """After each node, the best node so far by validation (working nodes only), with its scores.

    This is the node the agent would submit if it stopped there, so its probe score is what a
    monitor watches for divergence.
    """
    rows, best = [], None
    for _, n in nodes.iterrows():
        if n["status"] == "working" and pd.notna(n["val_score"]):
            if best is None or (n["val_score"] > best["val_score"] if higher_is_better
                                else n["val_score"] < best["val_score"]):
                best = n
        if best is not None:
            row = {"order": n["order"], "best_node": best["id"], "val_score": best["val_score"],
                   "probe_score": best["probe_score"]}
            if "test_score" in nodes:
                row["test_score"] = best["test_score"]
            rows.append(row)
    return pd.DataFrame(rows, columns=["order", "best_node", "val_score", "probe_score"]
                        + (["test_score"] if "test_score" in nodes else []))


def long_scores(frame: pd.DataFrame) -> pd.DataFrame:
    """`frame`'s score columns stacked into (order, split, score) rows for a chart, empty scores dropped."""
    names = {"val_score": "validation", "probe_score": "probe", "test_score": "test"}
    present = [c for c in names if c in frame]
    keep = [c for c in frame.columns if c not in present]
    out = frame.melt(id_vars=keep, value_vars=present, var_name="split", value_name="score")
    out["split"] = out["split"].map(names)
    return out.dropna(subset=["score"])


def tree_dot(nodes: pd.DataFrame, selected: str | None = None, final: str | None = None) -> str:
    """The search tree as Graphviz DOT: colour by status, label with scores, the selected node outlined."""
    lines = ['digraph tree {', 'rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", '
             'fontsize=10, fontcolor=white]; edge [color="#888888"];']
    for _, n in nodes.iterrows():
        scores = ""
        if pd.notna(n["val_score"]):
            scores = f"\\nval {n['val_score']:.4g}"
            if pd.notna(n["probe_score"]):
                scores += f" | probe {n['probe_score']:.4g}"
        colour = STATUS_COLOURS.get(n["status"], "#455a64")
        extra = ', penwidth=3, color="#ffb300"' if n["id"] in (selected, final) else ""
        star = " ★" if n["id"] == final else ""
        lines.append(f'"{n["id"]}" [label="{n["id"]} {n["operator"]}{star}{scores}", fillcolor="{colour}"{extra}];')
        if pd.notna(n["parent_id"]) and n["parent_id"]:
            lines.append(f'"{n["parent_id"]}" -> "{n["id"]}";')
    lines.append("}")
    return "\n".join(lines)


def history(run_dir: Path) -> pd.DataFrame:
    """Every queued intervention with its outcome: pending, applied or dropped (and why)."""
    outcomes = {}
    applied_path = run_dir / "applied.jsonl"
    if applied_path.exists():
        for line in applied_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                outcomes[rec["intervention"]["id"]] = rec
    rows = []
    for item in read_all(run_dir / "queue.jsonl"):
        rec = outcomes.get(item.id, {})
        rows.append({"queued_at": item.ts, "source": item.source, "action": item.action.value, "target": item.target,
                     "params": json.dumps(item.params) if item.params else "", "note": item.note or "",
                     "outcome": rec.get("outcome", "pending"), "reason": rec.get("reason") or "",
                     "applied_at": rec.get("applied_at"), "id": item.id})
    return pd.DataFrame(rows, columns=["queued_at", "source", "action", "target", "params", "note", "outcome",
                                       "reason", "applied_at", "id"])


def intervention_positions(hist: pd.DataFrame, nodes: pd.DataFrame) -> pd.DataFrame:
    """Applied interventions placed on the node axis: just after the last node finished before they applied."""
    applied = hist[hist["outcome"] == "applied"].copy()
    if applied.empty or nodes.empty:
        return applied.assign(order=pd.Series(dtype=float))
    finished = pd.to_datetime(nodes["finished_at"], utc=True, errors="coerce")
    applied["order"] = [float((finished <= t).sum()) - 0.5
                        for t in pd.to_datetime(applied["applied_at"], utc=True, errors="coerce")]
    return applied


def node_files(run_dir: Path, node_id: str, tail_chars: int = 4000) -> dict[str, str]:
    """A node's script and the end of its stdout and stderr, empty strings for missing files."""
    d = run_dir / "nodes" / node_id

    def read(name: str, tail: bool) -> str:
        """One file's text, or its last `tail_chars` characters."""
        path = d / name
        if not path.exists():
            return ""
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[-tail_chars:] if tail else text

    return {"script": read("solution.py", False), "stdout": read("stdout.txt", True),
            "stderr": read("stderr.txt", True)}


def log_event(run_dir: Path, session: str, event: str, **fields: Any) -> None:
    """Append one dashboard event (session start, node viewed, intervention queued) to dashboard_log.jsonl."""
    record = {"ts": now(), "session": session, "event": event, **fields}
    with (run_dir / LOG_NAME).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def queue_intervention(run_dir: Path, action: Action | str, target: str | None = None,
                       params: dict[str, Any] | None = None, note: str | None = None, source: str = "human",
                       session: str | None = None) -> Intervention:
    """Append a human intervention to queue.jsonl, and log it for C6 when a dashboard session is given."""
    item = Intervention(id=f"q-{uuid.uuid4().hex[:8]}", ts=now(), source=source, action=Action(action),
                        target=target or None, params=params or {}, note=note or None)
    append(run_dir / "queue.jsonl", item)
    if session:
        log_event(run_dir, session, "queue", intervention=item.id, action=item.action.value, target=item.target)
    return item


def read_step(run_dir: Path, step: int | None = None) -> dict | None:
    """The checkpoint at `step`, or the newest complete one."""
    if step is None:
        steps = complete_steps(run_dir)
        step = steps[-1] if steps else None
    return checkpoint.read(run_dir, step) if step is not None else None
