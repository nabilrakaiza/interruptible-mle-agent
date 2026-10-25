"""Validation-test gap: how optimistic the agent's own validation score is, per node, run and condition.

Role 3's analysis section (docs/experiments.md, process metrics). Reads each run's
latest complete checkpoint through imle.checkpoint, so it needs only what
checkpoint.py defines; nodes need `test_score` (filled by the stand-in evaluator, A1,
or role 1's grading). Nodes without one are skipped and counted.

The gap is measured so that a positive value means the validation score was better
than the test score (optimism), whatever the metric's direction:

    gap = val - test      when higher is better (AUC)
    gap = test - val      when lower is better (log loss, RMSLE)

Per run: the final node's gap (the submitted node, else the best by validation), the
best-validation node's gap, and the mean over working nodes with a test score. Per
condition and task: mean, standard deviation, n runs and a seeded bootstrap 95% CI.
Tasks are summarised separately, since their metrics are on different scales.

    python scripts/analyze_val_test_gap.py --runs-dir runs --out results/val_test_gap
    python scripts/analyze_val_test_gap.py --runs-dir runs --glob 'C5_*' --condition-key condition

Writes nodes.csv, runs.csv and summary.csv under --out.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from imle.metrics import node_table, summarise, working

RUN_COLUMNS = ["final_gap", "best_val_gap", "mean_gap"]


def node_gaps(nodes: pd.DataFrame) -> pd.DataFrame:
    """Working nodes with validation and test scores, with their gap; a positive gap means optimism."""
    scored = working(nodes, "val_score", "test_score").copy()
    sign = np.where(scored["higher_is_better"].astype(bool), 1.0, -1.0)
    scored["gap"] = sign * (scored["val_score"] - scored["test_score"])
    return scored


def run_gaps(nodes: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    """One row per run: final, best-validation and mean gaps, and how many nodes lacked a test score."""
    rows = []
    for run, group in nodes.groupby("run", sort=True):
        g = gaps[gaps["run"] == run]
        final = g[g["is_final"]] if g["is_final"].any() else g[g["is_best_val"]]
        rows.append({"run": run, "condition": group["condition"].iloc[0], "task": group["task"].iloc[0],
                     "seed": group["seed"].iloc[0], "final_gap": final["gap"].mean() if len(final) else np.nan,
                     "best_val_gap": g.loc[g["is_best_val"], "gap"].mean() if g["is_best_val"].any() else np.nan,
                     "mean_gap": g["gap"].mean() if len(g) else np.nan, "nodes_with_test": len(g),
                     "working_without_test": int(len(working(group, "val_score")) - len(g))})
    return pd.DataFrame(rows, columns=["run", "condition", "task", "seed", *RUN_COLUMNS, "nodes_with_test",
                                       "working_without_test"])


def analyse(run_dirs: list[Path], condition_key: str = "condition", seed: int = 0
            ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(nodes, runs, summary) tables for the given run folders."""
    nodes = node_table(run_dirs, condition_key)
    gaps = node_gaps(nodes)
    runs = run_gaps(nodes, gaps)
    summary = summarise(runs, ["condition", "task"], RUN_COLUMNS, seed=seed) if len(runs) else pd.DataFrame()
    return gaps, runs, summary


def main(argv: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Command-line entry point: write the validation-test gap tables to --out."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--glob", default="*", help="run folder names to include, under --runs-dir")
    parser.add_argument("--condition-key", default="condition", help="status.json field naming the condition")
    parser.add_argument("--seed", type=int, default=0, help="bootstrap seed")
    parser.add_argument("--out", type=Path, default=Path("results/val_test_gap"))
    args = parser.parse_args(argv)
    run_dirs = sorted(p for p in args.runs_dir.glob(args.glob) if p.is_dir())
    gaps, runs, summary = analyse(run_dirs, args.condition_key, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    gaps.to_csv(args.out / "nodes.csv", index=False)
    runs.to_csv(args.out / "runs.csv", index=False)
    summary.to_csv(args.out / "summary.csv", index=False)
    print(f"{len(runs)} runs, {len(gaps)} nodes with a test score")
    if len(summary):
        print(summary[["condition", "task", "final_gap_mean", "final_gap_n", "final_gap_ci_low", "final_gap_ci_high"]]
              .to_string(index=False))
    print(f"wrote {args.out}")
    return gaps, runs, summary


if __name__ == "__main__":
    main()
