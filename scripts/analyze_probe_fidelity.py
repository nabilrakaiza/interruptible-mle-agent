"""Probe fidelity: how well the probe split ranks nodes the way the test set does.

Role 3's analysis section (docs/experiments.md, process metrics). The probe is the
signal monitors (C4, C5, humans) steer by; this measures whether it is worth trusting.
Reads each run's latest complete checkpoint through imle.checkpoint, and uses working
nodes that have both a probe and a test score.

Per run:
    spearman   Spearman rank correlation between probe and test scores across nodes
               (NaN with fewer than 3 nodes)
    top_k      share of the k best nodes by probe that are among the k best by test
               (k = --k, capped at the number of nodes; "best" follows the metric's direction)
    val_spearman / val_top_k   the same for the validation score, for comparison

Per condition and task: mean, standard deviation, n runs and a seeded bootstrap 95% CI.

    python scripts/analyze_probe_fidelity.py --runs-dir runs --k 5 --out results/probe_fidelity

Writes runs.csv and summary.csv under --out.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from imle.metrics import node_table, spearman, summarise, top_k_agreement, working

RUN_COLUMNS = ["spearman", "top_k", "val_spearman", "val_top_k"]


def run_fidelity(nodes: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """One row per run: probe-test and validation-test rank agreement."""
    rows = []
    for run, group in nodes.groupby("run", sort=True):
        g = working(group, "probe_score", "test_score")
        v = working(group, "val_score", "test_score")
        hib = bool(group["higher_is_better"].iloc[0])
        rows.append({"run": run, "condition": group["condition"].iloc[0], "task": group["task"].iloc[0],
                     "seed": group["seed"].iloc[0], "nodes": len(g),
                     "spearman": spearman(g["probe_score"], g["test_score"]),
                     "top_k": top_k_agreement(g["probe_score"].tolist(), g["test_score"].tolist(), k, hib)
                     if len(g) else np.nan,
                     "val_spearman": spearman(v["val_score"], v["test_score"]),
                     "val_top_k": top_k_agreement(v["val_score"].tolist(), v["test_score"].tolist(), k, hib)
                     if len(v) else np.nan})
    return pd.DataFrame(rows, columns=["run", "condition", "task", "seed", "nodes", *RUN_COLUMNS])


def analyse(run_dirs: list[Path], k: int = 5, condition_key: str = "condition", seed: int = 0
            ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(runs, summary) tables for the given run folders."""
    runs = run_fidelity(node_table(run_dirs, condition_key), k)
    summary = summarise(runs, ["condition", "task"], RUN_COLUMNS, seed=seed) if len(runs) else pd.DataFrame()
    return runs, summary


def main(argv: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Command-line entry point: write the probe fidelity tables to --out."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--glob", default="*", help="run folder names to include, under --runs-dir")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--condition-key", default="condition", help="status.json field naming the condition")
    parser.add_argument("--seed", type=int, default=0, help="bootstrap seed")
    parser.add_argument("--out", type=Path, default=Path("results/probe_fidelity"))
    args = parser.parse_args(argv)
    run_dirs = sorted(p for p in args.runs_dir.glob(args.glob) if p.is_dir())
    runs, summary = analyse(run_dirs, args.k, args.condition_key, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    runs.to_csv(args.out / "runs.csv", index=False)
    summary.to_csv(args.out / "summary.csv", index=False)
    print(f"{len(runs)} runs")
    if len(summary):
        print(summary[["condition", "task", "spearman_mean", "spearman_n", "top_k_mean"]].to_string(index=False))
    print(f"wrote {args.out}")
    return runs, summary


if __name__ == "__main__":
    main()
