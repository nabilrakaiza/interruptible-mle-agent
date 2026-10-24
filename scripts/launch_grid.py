"""Run the experiment grid in configs/schedule.yaml, one run after another, resuming after crashes.

Each (condition, task, seed) goes through scripts/cloud_run.py, so a run with no
checkpoint starts, an unfinished one resumes, and a finished one is skipped. Calling
this again after a crash, a reboot or a lost session therefore continues the grid.

Several machines split the grid with --shard i/N: machine i takes every N-th run of the
list, so every machine works down the list in order of importance (C1 first). A
condition whose scripted policy is not implemented yet is reported as blocked and
skipped, instead of failing and retrying.

    python scripts/launch_grid.py --status                       # the whole grid: done, unfinished, to do
    python scripts/launch_grid.py --shard 0/3 --dry-run          # what machine 0 of 3 would run
    python scripts/launch_grid.py --shard 0/3                    # run it
    python scripts/launch_grid.py --only C1 --only spooky        # a subset (substring of condition or task)
    python scripts/launch_grid.py --shard 1/3 --sandbox subprocess --sync-to /content/drive/MyDrive/imle/runs
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cloud_run import state

from imle.controller import load_config, load_policies


@dataclass
class Run:
    """One cell of the grid."""

    index: int
    config: Path
    condition: str
    task: str
    seed: int

    @property
    def name(self) -> str:
        """The run folder's name, the same one cloud_run.py uses."""
        return f"{self.condition}_{self.task}_seed{self.seed}"


def grid(schedule: dict, configs_dir: Path) -> list[Run]:
    """Every run in the schedule, in its order: block by block, seed by seed, task by task."""
    runs = []
    for block in schedule["blocks"]:
        config = configs_dir / block["config"]
        condition = (yaml.safe_load(config.read_text(encoding="utf-8")) or {}).get("condition", config.stem)
        for seed in block["seeds"]:
            for task in schedule["tasks"]:
                runs.append(Run(len(runs), config, condition, task, int(seed)))
    return runs


def parse_shard(text: str) -> tuple[int, int]:
    """'i/N' as (i, N), checking 0 <= i < N."""
    i, _, n = text.partition("/")
    shard, count = int(i), int(n)
    if not 0 <= shard < count:
        raise argparse.ArgumentTypeError(f"shard {text}: need 0 <= i < N")
    return shard, count


def select(runs: list[Run], shard: tuple[int, int] | None, only: list[str]) -> list[Run]:
    """The runs this machine takes: its shard (by position in the full grid), filtered by --only."""
    if shard:
        runs = [r for r in runs if r.index % shard[1] == shard[0]]
    for word in only:
        runs = [r for r in runs if word in r.condition or word in r.task]
    return runs


def blocked(config: Path) -> str | None:
    """Why a condition cannot run yet (its policy has no decide), or None."""
    try:
        load_policies(load_config(config))
    except SystemExit as e:
        return str(e).split(". ")[0]
    except ImportError as e:
        return str(e)
    return None


def cloud_run_command(run: Run, args: argparse.Namespace, budget_hours: float, defaults: dict) -> list[str]:
    """The cloud_run.py command for one run."""
    cmd = [sys.executable, str(ROOT / "scripts" / "cloud_run.py"), "--config", str(run.config), "--task", run.task,
           "--seed", str(run.seed), "--budget-hours", str(budget_hours),
           "--sandbox", args.sandbox or defaults.get("sandbox", "docker"), "--runs-root", str(args.runs_root)]
    evaluator = args.evaluator or defaults.get("evaluator")
    cmd += ["--evaluator", evaluator] if evaluator else []
    cmd += ["--provider", args.provider] if args.provider else []
    cmd += ["--sync-to", args.sync_to] if args.sync_to else []
    return cmd


def main() -> None:
    """Command-line entry point: show the grid's status, or run this machine's share of it."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--schedule", type=Path, default=ROOT / "configs" / "schedule.yaml")
    parser.add_argument("--shard", type=parse_shard, help="i/N: this machine is number i (from 0) of N")
    parser.add_argument("--only", action="append", default=[], help="keep runs whose condition or task contains this")
    parser.add_argument("--runs-root", type=Path, help="override the schedule's runs_root")
    parser.add_argument("--budget-hours", type=float, help="override the schedule's budget_hours")
    parser.add_argument("--sandbox", choices=["docker", "subprocess"], help="override the schedule's sandbox")
    parser.add_argument("--evaluator", choices=["a1", "stand_in"], help="override the schedule's evaluator")
    parser.add_argument("--provider", choices=["openrouter", "gemini"])
    parser.add_argument("--sync-to", help="passed to cloud_run.py: copy each run here while it runs")
    parser.add_argument("--status", action="store_true", help="print where every selected run stands, then exit")
    parser.add_argument("--dry-run", action="store_true", help="print the commands, run nothing")
    args = parser.parse_args()

    schedule = yaml.safe_load(args.schedule.read_text(encoding="utf-8"))
    defaults = schedule.get("defaults") or {}
    budget = args.budget_hours or float(defaults.get("budget_hours", 2))
    args.runs_root = (args.runs_root or ROOT / defaults.get("runs_root", "runs/grid")).resolve()
    runs = select(grid(schedule, args.schedule.parent / "conditions"), args.shard, args.only)
    reasons = {c: blocked(c) for c in {r.config for r in runs}}

    if args.status:
        counts: dict[str, int] = {}
        for r in runs:
            how = "blocked" if reasons[r.config] else state(args.runs_root / r.name, budget)
            label = {"start": "to do", "resume": "unfinished", "done": "done", "blocked": "blocked"}[how]
            counts[label] = counts.get(label, 0) + 1
            print(f"{r.index:4d}  {label:10s}  {r.name}")
        print(" · ".join(f"{k}: {v}" for k, v in counts.items()) + f"  ({len(runs)} runs, {budget:g} h each)")
        return

    print(f"{len(runs)} runs, up to {len(runs) * budget:g} machine-hours at {budget:g} h each")
    failed = []
    for r in runs:
        if reasons[r.config]:
            print(f"skip {r.name}: blocked ({reasons[r.config]})")
            continue
        if state(args.runs_root / r.name, budget) == "done":
            continue
        cmd = cloud_run_command(r, args, budget, defaults)
        print(f"[{r.index}] {r.name}: {' '.join(cmd)}", flush=True)
        if args.dry_run:
            continue
        if subprocess.run(cmd, cwd=ROOT, check=False).returncode != 0:
            failed.append(r.name)
    if failed:
        print(f"{len(failed)} run(s) did not finish: {', '.join(failed)}. Run this command again to resume them.")
        sys.exit(1)


if __name__ == "__main__":
    main()
