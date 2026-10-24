"""Grade finished runs with MLE-bench: valid submission, score, above median, medals.

For every finished run (final checkpoint has `done`) this grades `submission.csv`, and
with top_k every `final/submission_<rank>.csv` too, against the competition's private
answers and medal thresholds, and writes `grade.json` into the run folder. These are
the outcome metrics of role 1's report section (scripts/outcomes.py aggregates them).

MLE-bench lives in its own virtual environment, deliberately apart from the agent's:
scripts run by the subprocess sandbox use the agent's interpreter and must not be able
to import mlebench and read private answers. So grading runs MLE-bench's Python as a
subprocess. Point to it with --mlebench-python or MLEBENCH_PYTHON (e.g. in .env):

    python scripts/grade.py runs/                       # every finished, ungraded run
    python scripts/grade.py runs/c4 --force             # grade again
    MLEBENCH_PYTHON=~/mle-bench/.venv/bin/python python scripts/grade.py runs/

Runs on tasks MLE-bench does not know (the toy smoke task) are reported and skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from imle import monitor

# Runs inside MLE-bench's interpreter: reads [[path, competition], ...] on stdin, prints one report each.
GRADER = r"""
import json, sys
from pathlib import Path
from mlebench.grade import grade_csv
from mlebench.registry import registry
data_dir = sys.argv[1]
reg = registry.set_data_dir(Path(data_dir)) if data_dir else registry
out = []
for path, comp in json.load(sys.stdin):
    try:
        out.append(grade_csv(Path(path), reg.get_competition(comp)).to_dict())
    except Exception as e:
        out.append({"error": f"{type(e).__name__}: {e}"})
print("@@GRADES@@" + json.dumps(out, default=str))
"""
MARKER = "@@GRADES@@"
KEEP = ("score", "valid_submission", "above_median", "any_medal", "gold_medal", "silver_medal", "bronze_medal",
        "median_threshold", "bronze_threshold", "silver_threshold", "gold_threshold", "is_lower_better", "error")


def submissions(run_dir: Path) -> list[Path]:
    """The run's final submission, then any top_k ones under final/, that exist."""
    files = [run_dir / "submission.csv"] + sorted((run_dir / "final").glob("submission_*.csv"))
    return [f for f in files if f.exists()]


def to_grade(run_dir: Path, force: bool) -> tuple[str, dict] | None:
    """The run's task and final status if it should be graded now, else None (unfinished, or graded already)."""
    ck = monitor.read_step(run_dir)
    if ck is None or not ck["status"].get("done"):
        return None
    if (run_dir / "grade.json").exists() and not force:
        return None
    return ck["status"].get("task"), ck["status"]


def run_grader(python: str, data_dir: str, items: list[tuple[Path, str]]) -> list[dict]:
    """Grade (submission, competition) pairs in one MLE-bench process; one report dict per pair."""
    if not items:
        return []
    proc = subprocess.run([python, "-c", GRADER, data_dir], input=json.dumps([[str(p), c] for p, c in items]),
                          capture_output=True, text=True, check=False)
    line = next((ln for ln in proc.stdout.splitlines() if ln.startswith(MARKER)), None)
    if line is None:
        raise SystemExit(f"MLE-bench grading failed (exit {proc.returncode}). Is {python} MLE-bench's Python?\n"
                         f"{proc.stderr[-2000:]}")
    return json.loads(line[len(MARKER):])


def summary(report: dict) -> dict:
    """The fields of an MLE-bench report that the analysis uses."""
    return {k: report[k] for k in KEEP if k in report}


def main() -> None:
    """Command-line entry point: grade every finished run under the given folders."""
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path, help="run folders, or folders holding them")
    parser.add_argument("--mlebench-python", default=os.environ.get("MLEBENCH_PYTHON", sys.executable),
                        help="MLE-bench's Python interpreter (default: $MLEBENCH_PYTHON)")
    parser.add_argument("--data-dir", default=os.environ.get("MLEBENCH_DATA_DIR", ""),
                        help="MLE-bench's data folder (default: $MLEBENCH_DATA_DIR, else MLE-bench's own default)")
    parser.add_argument("--force", action="store_true", help="grade runs that already have grade.json")
    args = parser.parse_args()

    runs = sorted({r for p in args.paths for r in ([p] if (p / "checkpoints").is_dir() else monitor.find_runs(p))})
    jobs, items = [], []
    for run_dir in runs:
        todo = to_grade(run_dir, args.force)
        if todo is None:
            continue
        task, status = todo
        files = submissions(run_dir)
        if not files:
            print(f"{run_dir}: finished without a submission")
        jobs.append((run_dir, task, status, files))
        items.extend((f, task) for f in files)

    reports = iter(run_grader(args.mlebench_python, args.data_dir, items))
    graded = 0
    for run_dir, task, status, files in jobs:
        per_file = [{"file": str(f.relative_to(run_dir)), **summary(next(reports))} for f in files]
        if per_file and all("error" in r for r in per_file):
            print(f"{run_dir}: not graded ({per_file[0]['error']})")
            continue
        result = {
            "task": task, "condition": status.get("condition"), "seed": status.get("seed"),
            "final_node": status.get("final_node"), "final_selection": status.get("final_selection"),
            "submitted": bool(per_file),
            **({k: v for k, v in per_file[0].items() if k != "file"} if per_file else
               {"valid_submission": False, "above_median": False, "any_medal": False}),
            "submissions": per_file,
            "graded_at": datetime.now(timezone.utc).isoformat(),
        }
        (run_dir / "grade.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        graded += 1
        medal = next((m for m in ("gold", "silver", "bronze") if result.get(f"{m}_medal")), None)
        print(f"{run_dir}: score {result.get('score')}, valid {result.get('valid_submission')}, "
              f"above median {result.get('above_median')}, medal {medal or 'none'}")
    print(f"graded {graded} run(s); {len(runs) - len(jobs)} skipped (unfinished or graded already)")


if __name__ == "__main__":
    main()
