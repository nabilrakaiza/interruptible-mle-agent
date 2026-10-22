import importlib.util
import json
import os
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from imle import checkpoint

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cloud_run", ROOT / "scripts" / "cloud_run.py")
cloud = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloud)


def args(**overrides) -> Namespace:
    """Launcher arguments for a real-task run, with overrides."""
    base = {
        "config": str(ROOT / "configs" / "conditions" / "c1_autonomous.yaml"), "task": "spooky-author-identification",
        "seed": 3, "provider": None, "evaluator": None, "sandbox": "subprocess", "name": None, "smoke": False, "dry_run": False,
        "nodes": 6, "minutes": 10.0, "budget_hours": None,
    }
    return Namespace(**{**base, **overrides})


def checkpointed(run_dir: Path, done: bool) -> None:
    """Give `run_dir` one complete checkpoint, finished or not."""
    checkpoint.write(run_dir, 0, {"nodes": {}, "higher_is_better": True}, [], {"done": done})


def test_name_state_and_command(tmp_path: Path):
    """The run name is fixed per condition, task and seed; the command starts, or resumes once checkpointed."""
    a = args()
    assert cloud.run_name(a) == "C1_spooky-author-identification_seed3"
    assert cloud.run_name(args(smoke=True, dry_run=True)) == "smoke_dry_seed3"
    run_dir = tmp_path / "C1_spooky-author-identification_seed3"
    assert cloud.state(run_dir) == "start"
    start = cloud.command(args(provider="gemini"), run_dir, "start")
    assert start[1:3] == ["-m", "imle.controller"] and start[-2:] == ["--provider", "gemini"]
    assert "--run-dir" in start and "--sandbox" in start
    checkpointed(run_dir, done=False)
    assert cloud.state(run_dir) == "resume"
    assert cloud.command(a, run_dir, "resume")[-2:] == ["--resume", str(run_dir)]
    checkpointed(run_dir, done=True)
    assert cloud.state(run_dir) == "done"


def test_budget_hours_continues_a_finished_run_once(tmp_path: Path):
    """A finished run with less budget than --budget-hours is resumed; once it has that much, it is done."""
    run_dir = tmp_path / "run"
    (run_dir).mkdir()
    (run_dir / "config.yaml").write_text("budget: {wall_clock_s: 7200}\n")
    checkpoint.write(run_dir, 0, {"nodes": {}, "higher_is_better": True}, [],
                     {"done": True, "search": {"extra_budget_s": 0.0}})
    assert cloud.state(run_dir) == "done" and cloud.state(run_dir, 2) == "done"
    assert cloud.state(run_dir, 4) == "resume"
    cmd = cloud.command(args(budget_hours=4.0), run_dir, "resume")
    assert cmd[-4:] == ["--budget-hours", "4.0", "--resume", str(run_dir)]
    checkpoint.write(run_dir, 1, {"nodes": {}, "higher_is_better": True}, [],
                     {"done": True, "search": {"extra_budget_s": 7200.0}})
    assert cloud.state(run_dir, 4) == "done"  # a retried command does not extend it again


def test_sync_copies_only_changes(tmp_path: Path):
    """A second sync copies nothing; a changed or new file is copied; nothing in the target is deleted."""
    src, dst = tmp_path / "src", tmp_path / "dst"
    (src / "a").mkdir(parents=True)
    (src / "a" / "x.txt").write_text("1")
    (src / "y.txt").write_text("2")
    assert cloud.sync(src, dst) == 2
    assert cloud.sync(src, dst) == 0
    (src / "y.txt").write_text("22")
    (src / "z.txt").write_text("3")
    (dst / "only_here.txt").write_text("keep")
    assert cloud.sync(src, dst) == 2
    assert (dst / "y.txt").read_text() == "22" and (dst / "only_here.txt").exists()


def test_restore_prefers_a_checkpointed_copy(tmp_path: Path):
    """An empty local folder is restored from the first source that has a checkpoint; a local run is left alone."""
    local = tmp_path / "local" / "r"
    empty, saved = tmp_path / "empty", tmp_path / "saved"
    (empty / "r").mkdir(parents=True)
    checkpointed(saved / "r", done=False)
    assert cloud.restore(local, [empty, saved]) == saved / "r"
    assert cloud.state(local) == "resume"
    assert cloud.restore(local, [saved]) is None  # already has a checkpoint


def test_dry_smoke_run_to_the_end_with_sync(tmp_path: Path, monkeypatch):
    """The launcher runs a dry smoke run to the end, copies it to the sync folder, and a rerun does nothing."""
    pytest.importorskip("sklearn")
    argv = ["cloud_run.py", "--smoke", "--dry-run", "--nodes", "2", "--seed", "5",
            "--runs-root", str(tmp_path / "local"), "--sync-to", str(tmp_path / "drive"), "--sync-every", "1"]
    monkeypatch.setattr(sys, "argv", argv)
    cwd = os.getcwd()
    try:
        with pytest.raises(SystemExit) as first:
            cloud.main()
        assert first.value.code == 0
        synced = tmp_path / "drive" / "smoke_dry_seed5"
        assert cloud.state(synced) == "done"
        assert json.loads((synced / "machine.jsonl").read_text().splitlines()[0])["event"] == "start"
        with pytest.raises(SystemExit) as again:
            cloud.main()
        assert again.value.code == 0
        assert len((synced / "machine.jsonl").read_text().splitlines()) == 1  # nothing ran the second time
    finally:
        os.chdir(cwd)
