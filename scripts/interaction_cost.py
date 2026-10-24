"""Interaction cost: how often monitors intervened, when, with what effect, and how much human time it took.

Role 4's analysis section (proposal Section 5: interventions per run, their timing, human
time per intervention in C6, and wall clock lost to abandoned nodes). Reads only run
folders: queue.jsonl, applied.jsonl, dashboard_log.jsonl and the latest checkpoint.

    timing         where in the run each applied intervention landed, as the share of the
                   run's nodes finished before it (0 = before the first node, 1 = at the end)
    human time     for each intervention queued from the dashboard, the time from the start
                   of that session, or from the same session's previous intervention, to
                   queueing it: the time a person spent looking before acting
    lost wall clock  abandon is cut from scope, so this is always 0 and reported as such

    python scripts/interaction_cost.py runs/grid                          # print the tables
    python scripts/interaction_cost.py runs/grid --out analysis/interaction
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from imle import monitor


def read_log(run_dir: Path) -> pd.DataFrame:
    """The run's dashboard events, oldest first (empty when nobody used the dashboard on it)."""
    path = run_dir / monitor.LOG_NAME
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] \
        if path.exists() else []
    df = pd.DataFrame(rows, columns=["ts", "session", "event", "intervention"] if not rows else None)
    if not df.empty:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, format="ISO8601")
        df = df.sort_values("ts")
    return df


def human_seconds(log: pd.DataFrame) -> dict[str, float]:
    """Seconds each dashboard intervention took: since its session started, or since that session's last one."""
    out = {}
    if log.empty:
        return out
    for _, session in log.groupby("session"):
        since = session["ts"].iloc[0]
        for _, e in session.iterrows():
            if e["event"] == "queue":
                out[e["intervention"]] = (e["ts"] - since).total_seconds()
                since = e["ts"]
    return out


def run_interventions(run_dir: Path) -> pd.DataFrame:
    """One row per queued intervention in the run, with outcome, timing and human time."""
    ck = monitor.read_step(run_dir)
    if ck is None:
        return pd.DataFrame()
    hist = monitor.history(run_dir)
    if hist.empty:
        return hist
    nodes = monitor.node_frame(ck)
    hist = hist.merge(monitor.intervention_positions(hist, nodes)[["id", "order"]], on="id", how="left")
    hist["timing"] = (hist["order"] + 0.5) / max(len(nodes), 1)
    seconds = human_seconds(read_log(run_dir))
    hist["human_s"] = hist["id"].map(seconds)
    status = ck["status"]
    return hist.assign(run=run_dir.name, condition=status.get("condition"), task=status.get("task"),
                       seed=status.get("seed"), source_kind=hist["source"].where(hist["source"] == "human", "policy"))


def per_run(run_dir: Path, items: pd.DataFrame) -> dict:
    """One run's counts: interventions queued, applied and dropped, by action, and its human time."""
    status = (monitor.read_step(run_dir) or {"status": {}})["status"]
    applied = items[items["outcome"] == "applied"] if not items.empty else items
    row = {"run": run_dir.name, "condition": status.get("condition"), "task": status.get("task"),
           "seed": status.get("seed"), "queued": len(items), "applied": len(applied),
           "dropped": int((items["outcome"] == "dropped").sum()) if not items.empty else 0,
           "first_applied_at": round(applied["timing"].min(), 3) if not applied.empty else None,
           "human_minutes": round(items["human_s"].sum() / 60, 2) if not items.empty else 0.0,
           "lost_wall_clock_s": 0.0}
    for action in ("prune", "redirect", "override", "inject", "correct", "rebudget"):
        row[action] = int((applied["action"] == action).sum()) if not applied.empty else 0
    return row


def main() -> None:
    """Command-line entry point: print the interaction-cost tables, and write them with --out."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path, help="run folders, or folders holding them")
    parser.add_argument("--out", type=Path, help="write interventions.csv, runs.csv, conditions.csv, summary.md")
    args = parser.parse_args()

    dirs = sorted({r for p in args.paths for r in ([p] if (p / "checkpoints").is_dir() else monitor.find_runs(p))})
    frames, rows = [], []
    for d in dirs:
        items = run_interventions(d)
        rows.append(per_run(d, items))
        if not items.empty:
            frames.append(items)
    runs = pd.DataFrame(rows)
    if runs.empty:
        raise SystemExit("no runs found")
    items = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["condition", "source_kind", "outcome", "timing", "human_s", "action", "reason"])

    conditions = runs.groupby("condition", dropna=False).agg(
        runs=("run", "count"), queued_per_run=("queued", "mean"), applied_per_run=("applied", "mean"),
        dropped_per_run=("dropped", "mean"), first_applied_at=("first_applied_at", "median"),
        human_minutes_per_run=("human_minutes", "mean"), lost_wall_clock_s=("lost_wall_clock_s", "sum"),
    ).round(3).reset_index()
    sections = [f"# Interaction cost\n\n{len(runs)} runs, {len(items)} queued interventions.\n",
                "## By condition\n", monitor.md_table(conditions)]
    if not items.empty:
        by_action = items.groupby(["condition", "source_kind", "action", "outcome"]).size().rename("n").reset_index()
        sections += ["## By action and outcome\n", monitor.md_table(by_action)]
        dropped = items[items["outcome"] == "dropped"].groupby("reason").size().rename("n").reset_index()
        sections += ["## Why interventions were dropped\n", monitor.md_table(dropped)]
        human = items.dropna(subset=["human_s"])
        if not human.empty:
            stats = human.groupby("condition")["human_s"].describe()[["count", "50%", "mean", "max"]].round(1)
            sections += ["## Human seconds per intervention (dashboard)\n",
                         monitor.md_table(stats.rename(columns={"50%": "median"}).reset_index())]
    sections += ["## Runs\n", monitor.md_table(runs)]
    summary = "\n".join(sections)
    print(summary)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        items.to_csv(args.out / "interventions.csv", index=False)
        runs.to_csv(args.out / "runs.csv", index=False)
        conditions.to_csv(args.out / "conditions.csv", index=False)
        (args.out / "summary.md").write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
