"""Start or resume one run on Colab, Kaggle or any machine that can lose its session.

One command does the right thing however many times it is called:

    - If the run folder has no checkpoint yet, the run starts.
    - If it has one, the run resumes from it (the controller's --resume).
    - If the run already finished, nothing runs.

While the run goes, the run folder is copied to `--sync-to` every `--sync-every`
seconds and once more at the end. On a fresh machine, a run that exists only in
`--sync-to` (or in `--restore-from`) is copied back first, so after a Colab
disconnect the same command continues where the last copy left off. A checkpoint
copied half-written is harmless: resume skips incomplete checkpoints.

Copies are incremental (only files whose size or time changed), so syncing a run
every two minutes stays cheap.

Colab, with the run on local disk and a copy on Drive:

    python scripts/cloud_run.py --config configs/conditions/c1_autonomous.yaml \\
        --task spooky-author-identification --seed 0 \\
        --runs-root /content/runs --sync-to /content/drive/MyDrive/imle/runs

Kaggle, where /kaggle/working is kept as the notebook's output, restoring from the
output of an earlier version attached as input:

    python scripts/cloud_run.py ... --runs-root /kaggle/working/runs \\
        --restore-from /kaggle/input/<earlier-version>/runs

Toy task instead of a real one (no evaluator or Kaggle data needed): add --smoke,
and --dry-run for canned replies without an API key.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

from imle.controller import latest_complete_checkpoint

ROOT = Path(__file__).resolve().parents[1]


def run_name(args: argparse.Namespace) -> str:
    """The run folder's name: fixed for a (condition, task, seed), so every call finds the same run."""
    if args.name:
        return args.name
    if args.smoke:
        return f"smoke_{'dry' if args.dry_run else args.provider or 'gemini'}_seed{args.seed}"
    condition = (yaml.safe_load(Path(args.config).read_text()) or {}).get("condition", "run")
    return f"{condition}_{args.task}_seed{args.seed}"


def state(run_dir: Path) -> str:
    """"start" (no checkpoint yet), "resume" (unfinished) or "done"."""
    ck = latest_complete_checkpoint(run_dir) if run_dir.exists() else None
    if ck is None:
        return "start"
    return "done" if ck["status"].get("done") else "resume"


def sync(src: Path, dst: Path) -> int:
    """Copy files from `src` to `dst` whose size or modification time differ. Returns how many were copied.

    Never deletes anything in `dst`. Files that vanish mid-copy (a checkpoint being
    replaced) are skipped; the next sync picks up their replacement.
    """
    copied = 0
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        target = dst / path.relative_to(src)
        try:
            stat = path.stat()
            if target.exists():
                old = target.stat()
                if old.st_size == stat.st_size and int(old.st_mtime) >= int(stat.st_mtime):
                    continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied += 1
        except FileNotFoundError:
            continue
    return copied


def restore(run_dir: Path, sources: list[Path]) -> Path | None:
    """Copy the run back from the first source that has a checkpoint of it, if the local copy has none."""
    if state(run_dir) != "start":
        return None
    for source in sources:
        candidate = source / run_dir.name
        if candidate.exists() and state(candidate) != "start":
            sync(candidate, run_dir)
            return candidate
    return None


def command(args: argparse.Namespace, run_dir: Path, how: str) -> list[str]:
    """The controller (or smoke run) command line that starts or resumes `run_dir`."""
    if args.smoke:
        cmd = [sys.executable, str(ROOT / "scripts" / "smoke_run.py")]
        if how == "resume":
            return [*cmd, "--resume", str(run_dir)]
        cmd += ["--run-dir", str(run_dir), "--seed", str(args.seed), "--nodes", str(args.nodes),
                "--minutes", str(args.minutes)]
        cmd += ["--dry-run"] if args.dry_run else ["--provider", args.provider or "gemini"]
        return cmd
    cmd = [sys.executable, "-m", "imle.controller", "--sandbox", args.sandbox]
    if how == "resume":
        return [*cmd, "--resume", str(run_dir)]
    cmd += ["--config", args.config, "--task", args.task, "--seed", str(args.seed), "--run-dir", str(run_dir)]
    cmd += ["--evaluator", args.evaluator] if args.evaluator else []
    return [*cmd, "--provider", args.provider] if args.provider else cmd


def launch(args: argparse.Namespace) -> int:
    """Restore if needed, then start or resume the run, syncing it while it goes. Returns the exit code."""
    run_dir = (Path(args.runs_root) / run_name(args)).resolve()
    sources = [Path(p) for p in (args.sync_to, args.restore_from) if p]
    if source := restore(run_dir, sources):
        print(f"restored {run_dir.name} from {source}")

    for attempt in range(args.retries + 1):
        how = state(run_dir)
        if how == "done":
            print(f"{run_dir.name} has finished; nothing to run")
            break
        cmd = command(args, run_dir, how)
        print(f"{how} {run_dir.name} (attempt {attempt + 1}): {' '.join(cmd)}", flush=True)
        process = subprocess.Popen(cmd, cwd=ROOT)
        last = time.monotonic()
        while process.poll() is None:
            time.sleep(1)
            if args.sync_to and time.monotonic() - last >= args.sync_every:
                sync(run_dir, Path(args.sync_to) / run_dir.name)
                last = time.monotonic()
        if args.sync_to and run_dir.exists():
            sync(run_dir, Path(args.sync_to) / run_dir.name)
        if process.returncode == 0:
            break
        if attempt < args.retries:
            print(f"exited with code {process.returncode}; resuming in {args.retry_wait:.0f}s", flush=True)
            time.sleep(args.retry_wait)
    final = state(run_dir)
    print(f"{run_dir.name}: {final}")
    return 0 if final == "done" else 1


def main() -> None:
    """Parse arguments and launch."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--config", help="condition file (not needed with --smoke)")
    parser.add_argument("--task", help="MLE-bench competition ID (not needed with --smoke)")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--provider", choices=["openrouter", "gemini"], help="override llm.provider for a new run")
    parser.add_argument("--evaluator", choices=["a1", "stand_in"],
                        help="stand_in: the temporary MLE-bench evaluator, until role 3's A1 exists")
    parser.add_argument("--sandbox", choices=["docker", "subprocess"], default="subprocess",
                        help="subprocess by default: Colab and Kaggle cannot run Docker")
    parser.add_argument("--runs-root", default=str(ROOT / "runs"), help="where the run folder lives while it runs")
    parser.add_argument("--name", help="run folder name; default <condition>_<task>_seed<seed>")
    parser.add_argument("--sync-to", help="folder to copy the run to while it runs, and to restore it from")
    parser.add_argument("--restore-from", help="read-only folder to restore an unfinished run from")
    parser.add_argument("--sync-every", type=float, default=120, help="seconds between copies (default 120)")
    parser.add_argument("--retries", type=int, default=2,
                        help="times to resume after the run exits with an error, such as an LLM outage")
    parser.add_argument("--retry-wait", type=float, default=600, help="seconds to wait before each retry")
    parser.add_argument("--smoke", action="store_true", help="the toy task instead of a real one")
    parser.add_argument("--dry-run", action="store_true", help="with --smoke: canned replies, no API key")
    parser.add_argument("--nodes", type=int, default=6, help="with --smoke: node cap")
    parser.add_argument("--minutes", type=float, default=10, help="with --smoke: time budget")
    args = parser.parse_args()
    if not args.smoke and not (args.config and args.task):
        parser.error("--config and --task are required unless --smoke is given")
    os.chdir(ROOT)
    sys.exit(launch(args))


if __name__ == "__main__":
    main()
