"""Outcome metrics per condition: valid submission, above median and any medal rates, with 95% CIs.

Role 1's outcome section. Reads each run's grade.json (written by scripts/grade.py) and
its latest checkpoint. Intervals are percentile bootstraps over runs (2000 resamples,
seeded), as the proposal requires; with a handful of runs they are wide, and rankings
whose intervals overlap are not claimed.

Two post-hoc rows come from the C1 runs' trees, with the task's thresholds from grade.json
and each node's test score (graded by the evaluator for analysis, never shown to an agent):

    C2 (post hoc)   oracle final selection: the working node with the best test score
    C3 (post hoc)   top-k hedge: the best test score among the top `k` nodes by validation

    python scripts/outcomes.py runs/grid                         # print the tables
    python scripts/outcomes.py runs/grid --out analysis/outcomes # also write CSVs and summary.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from imle import monitor
from imle.controller import ranked
from imle.tree import Tree

METRICS = ("valid_submission", "above_median", "any_medal")


def medal_flags(score: float | None, grade: dict) -> dict:
    """MLE-bench's verdicts for a score, using the thresholds in a run's grade.json (score rounded to 5 places)."""
    if score is None or "median_threshold" not in grade:
        return {"valid_submission": False, "above_median": False, "any_medal": False, "score": None}
    s, lower = round(float(score), 5), grade.get("is_lower_better", False)

    def reaches(threshold: float) -> bool:
        """Whether the score is at least as good as `threshold`."""
        return s <= threshold if lower else s >= threshold

    return {"valid_submission": True, "score": s,
            "above_median": s < grade["median_threshold"] if lower else s > grade["median_threshold"],
            "any_medal": any(reaches(grade[f"{m}_threshold"]) for m in ("gold", "silver", "bronze"))}


def post_hoc(tree: Tree, grade: dict, k: int) -> list[tuple[str, dict]]:
    """C2 and C3 verdicts for one C1 run's tree."""
    graded = [n for n in ranked(tree) if n.test_score is not None]
    if not graded:
        return []
    better = min if grade.get("is_lower_better") else max
    oracle = better(n.test_score for n in graded)
    hedge = better(n.test_score for n in graded[:k])
    return [("C2 (post hoc)", medal_flags(oracle, grade)), (f"C3 (post hoc, k={k})", medal_flags(hedge, grade))]


def collect(run_dirs: list[Path], k: int) -> pd.DataFrame:
    """One row per graded run (plus C2 and C3 rows for each C1 run)."""
    rows = []
    for run_dir in run_dirs:
        path = run_dir / "grade.json"
        if not path.exists():
            continue
        grade = json.loads(path.read_text(encoding="utf-8"))
        base = {"run": run_dir.name, "task": grade.get("task"), "seed": grade.get("seed")}
        rows.append({**base, "condition": grade.get("condition"), "score": grade.get("score"),
                     **{m: bool(grade.get(m)) for m in METRICS}})
        if grade.get("condition") == "C1":
            ck = monitor.read_step(run_dir)
            if ck is not None:
                for condition, flags in post_hoc(Tree.model_validate(ck["tree"]), grade, k):
                    rows.append({**base, "condition": condition, **flags})
    return pd.DataFrame(rows, columns=["run", "task", "seed", "condition", "score", *METRICS])


def bootstrap_ci(values: np.ndarray, samples: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% percentile bootstrap interval of the mean of `values`."""
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = rng.choice(values, (samples, len(values))).mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def rates(rows: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Each metric's rate (as %) with its 95% bootstrap CI, per group; per task also the mean score."""
    out = []
    for key, group in rows.groupby(by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(by, key), runs=len(group))
        if "task" in by:
            row["mean_score"] = round(group["score"].astype(float).mean(), 5)
        for m in METRICS:
            values = group[m].astype(float).to_numpy()
            lo, hi = bootstrap_ci(values)
            row[m] = f"{values.mean() * 100:.0f}% [{lo * 100:.0f}, {hi * 100:.0f}]"
        out.append(row)
    return pd.DataFrame(out)


def main() -> None:
    """Command-line entry point: print the outcome tables, and write them with --out."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path, help="run folders, or folders holding them")
    parser.add_argument("--top-k", type=int, default=3, help="k for the post-hoc C3 row (default 3)")
    parser.add_argument("--out", type=Path, help="write runs.csv, conditions.csv and summary.md here")
    args = parser.parse_args()

    dirs = sorted({r for p in args.paths for r in ([p] if (p / "checkpoints").is_dir() else monitor.find_runs(p))})
    rows = collect(dirs, args.top_k)
    if rows.empty:
        raise SystemExit("no graded runs found: run scripts/grade.py first")
    by_condition = rates(rows, ["condition"])
    by_task = rates(rows, ["condition", "task"])
    summary = "\n".join([
        f"# Outcomes\n\n{rows['run'].nunique()} graded runs. Rates with 95% bootstrap intervals over runs.\n",
        "## By condition\n", monitor.md_table(by_condition),
        "## By condition and task\n", monitor.md_table(by_task),
    ])
    print(summary)
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        rows.to_csv(args.out / "runs.csv", index=False)
        by_condition.to_csv(args.out / "conditions.csv", index=False)
        by_task.to_csv(args.out / "tasks.csv", index=False)
        (args.out / "summary.md").write_text(summary, encoding="utf-8")


if __name__ == "__main__":
    main()
