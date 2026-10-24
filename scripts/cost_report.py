"""API cost and tokens per node, per run and per condition, and a projection for the whole grid.

Role 1's cost section. Reads only run folders: llm_calls.jsonl (one record per call,
with tokens and the cost OpenRouter reported) and the latest checkpoint (nodes, elapsed
time, condition, task).

Free models report a cost of 0, so every run also gets a reference cost: its tokens at
the experiment model's listed price (imle.llm.PRICES, overridable with --price-in and
--price-out, USD per million tokens). The projection multiplies the pilots' reference
cost per hour by the runs and budget in configs/schedule.yaml, per task where the pilots
cover the task and from all pilots otherwise.

    python scripts/cost_report.py runs/                          # every run under runs/
    python scripts/cost_report.py runs/grid --out analysis/cost  # also write CSVs and summary.md
    python scripts/cost_report.py runs/minimax runs/nemotron --project configs/schedule.yaml
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

from imle import llm, monitor


def read_calls(run_dir: Path) -> list[dict]:
    """The run's LLM call records, without prompts and completions (which can be large)."""
    path = run_dir / "llm_calls.jsonl"
    if not path.exists():
        return []
    calls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            calls.append({k: v for k, v in rec.items() if k not in ("prompt", "completion")})
    return calls


def run_row(run_dir: Path, price_in: float, price_out: float) -> dict | None:
    """One run's tokens, costs and size, or None when it has no checkpoint."""
    ck = monitor.read_step(run_dir)
    if ck is None:
        return None
    calls = read_calls(run_dir)
    status = ck["status"]
    nodes = len(ck["tree"].get("nodes", {}))
    tokens_in = sum(c.get("input_tokens") or 0 for c in calls)
    tokens_out = sum(c.get("output_tokens") or 0 for c in calls)
    reported = [c["cost_usd"] for c in calls if c.get("cost_usd") is not None]
    hours = (status.get("elapsed_s") or 0) / 3600
    served = Counter((c.get("sampling_params") or {}).get("served_by") for c in calls)
    served.pop(None, None)
    reference = (tokens_in * price_in + tokens_out * price_out) / 1e6
    return {
        "run": run_dir.name,
        "condition": status.get("condition"),
        "task": status.get("task"),
        "seed": status.get("seed"),
        "model": ", ".join(sorted({c.get("model", "?") for c in calls})),
        "done": bool(status.get("done")),
        "hours": round(hours, 3),
        "nodes": nodes,
        "calls": len(calls),
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "tokens_per_node": round((tokens_in + tokens_out) / nodes) if nodes else None,
        "cost_usd": round(sum(reported), 4) if reported else None,
        "reference_cost_usd": round(reference, 4),
        "reference_cost_per_hour": round(reference / hours, 4) if hours else None,
        "served_by": ", ".join(f"{k} {v}" for k, v in served.most_common()),
    }


def by_condition(runs: pd.DataFrame) -> pd.DataFrame:
    """Per condition: runs, mean nodes, tokens per node, cost per run (reported and reference), total cost."""
    return runs.groupby("condition", dropna=False).agg(
        runs=("run", "count"),
        mean_hours=("hours", "mean"),
        mean_nodes=("nodes", "mean"),
        tokens_per_node=("tokens_per_node", "mean"),
        mean_cost_usd=("cost_usd", "mean"),
        mean_reference_cost_usd=("reference_cost_usd", "mean"),
        total_cost_usd=("cost_usd", "sum"),
    ).round(4).reset_index()


def project(runs: pd.DataFrame, schedule_path: Path) -> pd.DataFrame:
    """Reference cost of every run in the schedule: the pilots' cost per hour (per task if known) times the budget."""
    schedule = yaml.safe_load(schedule_path.read_text(encoding="utf-8"))
    hours = float((schedule.get("defaults") or {}).get("budget_hours", 2))
    rate = runs.dropna(subset=["reference_cost_per_hour"])
    overall = rate["reference_cost_per_hour"].mean() if not rate.empty else float("nan")
    per_task = rate.groupby("task")["reference_cost_per_hour"].mean().to_dict()
    seeds = sum(len(b["seeds"]) for b in schedule["blocks"])
    rows = []
    for task in schedule["tasks"]:
        per_hour = per_task.get(task, overall)
        rows.append({"task": task, "runs": seeds, "hours_each": hours, "cost_per_hour": round(per_hour, 4),
                     "from": "this task's pilots" if task in per_task else "all pilots",
                     "projected_usd": round(per_hour * hours * seeds, 2)})
    return pd.DataFrame(rows)


def main() -> None:
    """Command-line entry point: print the cost tables, and write them with --out."""
    default_in, default_out = llm.PRICES[llm.DEFAULT_MODELS["openrouter"]]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path, help="run folders, or folders holding them")
    parser.add_argument("--price-in", type=float, default=default_in, help="USD per million input tokens")
    parser.add_argument("--price-out", type=float, default=default_out, help="USD per million output tokens")
    parser.add_argument("--project", type=Path, help="a schedule (configs/schedule.yaml) to project the cost of")
    parser.add_argument("--out", type=Path, help="write runs.csv, conditions.csv, projection.csv and summary.md here")
    args = parser.parse_args()

    dirs = sorted({r for p in args.paths for r in ([p] if (p / "checkpoints").is_dir() else monitor.find_runs(p))})
    runs = pd.DataFrame([r for d in dirs if (r := run_row(d, args.price_in, args.price_out))])
    if runs.empty:
        raise SystemExit("no runs found")
    sections = [
        f"# Cost\n\nReference price: ${args.price_in}/M input, ${args.price_out}/M output tokens.",
        "## Runs\n\n" + monitor.md_table(runs.drop(columns=["served_by"])),
        "## By condition\n\n" + monitor.md_table(by_condition(runs)),
    ]
    projection = None
    if args.project:
        projection = project(runs, args.project)
        sections.append(f"## Projection for {args.project.name}\n\n" + monitor.md_table(projection)
                        + f"\n\nTotal: ${projection['projected_usd'].sum():.2f} for {projection['runs'].sum()} runs.")
    summary = "\n\n".join(sections) + "\n"
    print(summary)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        runs.to_csv(args.out / "runs.csv", index=False)
        by_condition(runs).to_csv(args.out / "conditions.csv", index=False)
        if projection is not None:
            projection.to_csv(args.out / "projection.csv", index=False)
        (args.out / "summary.md").write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
