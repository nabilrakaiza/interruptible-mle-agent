"""Download Kaggle sessions' runs into runs/kaggle/, check them, and grade the finished ones.

Each session of configs/kaggle_sessions.yaml runs in notebook imle-slot-<(s - 1) % 5 + 1>, and
only a notebook's latest version can be downloaded, so collect a round before starting the next.
The notebook writes session.json next to the runs; a slot whose latest output is another session
is reported and skipped, never copied.

    python scripts/kaggle_collect.py --round 1                    # sessions 1-5
    python scripts/kaggle_collect.py --session 7 --session 8      # particular sessions
    python scripts/kaggle_collect.py --round 1 --test             # the 15-minute test runs
    python scripts/kaggle_collect.py --round 1 --no-grade         # download and check only

The Kaggle CLI comes from $KAGGLE_BIN, else `kaggle` on the PATH; it uses your own token. Grading
needs MLE-bench's Python ($MLEBENCH_PYTHON or --mlebench-python), as scripts/grade.py does.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cloud_run import state


def sessions_of_round(plan: dict, round_no: int) -> list[int]:
    """The sessions a round starts: one per slot, in order."""
    slots = plan["slots"]
    return [s for s in range((round_no - 1) * slots + 1, round_no * slots + 1) if s in plan["sessions"]]


def run_names(plan: dict, session: int, test: bool) -> list[str]:
    """The run folder names a session writes, as the notebook names them."""
    entry = plan["sessions"][session]
    config = ROOT / "configs" / "conditions" / entry["config"]
    condition = yaml.safe_load(config.read_text(encoding="utf-8"))["condition"]
    return [f"{'test_' if test else ''}{condition}_{task}_seed{entry['seed']}" for task in plan["tasks"]]


def download(kaggle: str, ref: str, dest: Path) -> None:
    """The notebook's latest output, into dest: session.json and runs.tar.gz unpacked, else every file.

    The CLI fetches files one by one, thousands per session, so the notebook packs the runs into one
    archive; outputs from before it did are downloaded file by file. Pages of 200 (the CLI's default is
    20) keep that under Kaggle's request limit.
    """
    base = [kaggle, "kernels", "output", ref, "-p", str(dest), "-o", "-q", "--page-size", "200"]
    subprocess.run([*base, "--file-pattern", r"^(session\.json|runs\.tar\.gz)$"], check=True)
    archive = dest / "runs.tar.gz"
    if archive.exists():
        subprocess.run(["tar", "-xzf", str(archive), "-C", str(dest)], check=True)
    else:
        subprocess.run(base, check=True)


def collect(plan: dict, session: int, args: argparse.Namespace) -> list[Path]:
    """Download one session, copy its runs into runs_root, and return the folders now there."""
    slot = (session - 1) % plan["slots"] + 1
    ref = f"{args.user}/imle-slot-{slot}"
    with tempfile.TemporaryDirectory() as tmp:
        try:
            download(args.kaggle, ref, Path(tmp))
        except subprocess.CalledProcessError as e:
            print(f"session {session}: download of {ref} failed ({e})")
            return []
        info_path = Path(tmp) / "session.json"
        info = json.loads(info_path.read_text()) if info_path.exists() else {}
        if info.get("session") != session or bool(info.get("test")) != args.test:
            print(f"session {session}: {ref}'s latest output is session {info.get('session', '?')}"
                  f"{' (test)' if info.get('test') else ''}, not this one; skipped")
            return []
        copied = []
        for name in run_names(plan, session, args.test):
            src = Path(tmp) / "runs" / name
            if not src.is_dir():
                print(f"session {session}: {name} is missing from the output")
                continue
            dst = args.runs_root / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            copied.append(dst)
        print(f"session {session} ({ref}, code {info.get('commit', '?')[:7]}): exit codes {info.get('exit_codes')}")
        return copied


def main() -> None:
    """Command-line entry point: collect the chosen sessions, report where each run stands, and grade."""
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--round", type=int, action="append", default=[], help="a round's sessions (repeatable)")
    parser.add_argument("--session", type=int, action="append", default=[], help="one session (repeatable)")
    parser.add_argument("--test", action="store_true", help="the notebook's TEST runs (test_ names)")
    parser.add_argument("--user", default="nabilrakaizaabror", help="Kaggle user owning the imle-slot notebooks")
    parser.add_argument("--kaggle", default=os.environ.get("KAGGLE_BIN", "kaggle"), help="the Kaggle CLI")
    parser.add_argument("--plan", type=Path, default=ROOT / "configs" / "kaggle_sessions.yaml")
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs" / "kaggle")
    parser.add_argument("--mlebench-python", default=os.environ.get("MLEBENCH_PYTHON"))
    parser.add_argument("--no-grade", action="store_true", help="download and check only")
    args = parser.parse_args()

    plan = yaml.safe_load(args.plan.read_text(encoding="utf-8"))
    sessions = sorted({*args.session, *(s for r in args.round for s in sessions_of_round(plan, r))})
    if not sessions:
        parser.error("give --round or --session")
    args.runs_root.mkdir(parents=True, exist_ok=True)

    budget = 0.25 if args.test else plan["budget_hours"]
    done = []
    for session in sessions:
        for run_dir in collect(plan, session, args):
            how = state(run_dir, budget)
            print(f"  {run_dir.name}: {'finished' if how == 'done' else 'unfinished, run the session again'}")
            if how == "done":
                done.append(run_dir)

    if done and not args.no_grade:
        cmd = [sys.executable, str(ROOT / "scripts" / "grade.py"), *map(str, done), "--force"]
        cmd += ["--mlebench-python", args.mlebench_python] if args.mlebench_python else []
        subprocess.run(cmd, cwd=ROOT, check=False)


if __name__ == "__main__":
    main()
