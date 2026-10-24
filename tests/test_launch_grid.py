import argparse
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from imle import checkpoint

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("launch_grid", ROOT / "scripts" / "launch_grid.py")
launch_grid = importlib.util.module_from_spec(spec)
sys.modules["launch_grid"] = launch_grid  # its dataclass looks its module up while being defined
spec.loader.exec_module(launch_grid)

SCHEDULE = {"tasks": ["a", "b"], "blocks": [{"config": "c1_autonomous.yaml", "seeds": [0, 1]},
                                            {"config": "c5_finding_correction.yaml", "seeds": [0]}]}


def test_grid_order_and_names():
    """Blocks in order, then seeds, then tasks; names match cloud_run.py's."""
    runs = launch_grid.grid(SCHEDULE, ROOT / "configs" / "conditions")
    assert [r.name for r in runs] == ["C1_a_seed0", "C1_b_seed0", "C1_a_seed1", "C1_b_seed1", "C5_a_seed0",
                                      "C5_b_seed0"]
    assert [r.index for r in runs] == list(range(6))


def test_shards_split_the_grid_by_position():
    """Shards are disjoint, cover the grid, and each starts at the top of the list."""
    runs = launch_grid.grid(SCHEDULE, ROOT / "configs" / "conditions")
    shards = [launch_grid.select(runs, (i, 3), []) for i in range(3)]
    assert sorted(r.index for s in shards for r in s) == list(range(6))
    assert [r.index for r in shards[1]] == [1, 4]
    assert [r.name for r in launch_grid.select(runs, None, ["C1", "b"])] == ["C1_b_seed0", "C1_b_seed1"]
    assert launch_grid.parse_shard("2/3") == (2, 3)
    with pytest.raises(argparse.ArgumentTypeError):
        launch_grid.parse_shard("3/3")


def no_decide_policy(monkeypatch, conditions: Path) -> Path:
    """A condition whose listed policy module has no decide(), like C5 before role 3's code.

    The config goes in `conditions`, with base.yaml next to that folder as load_config expects.
    """
    monkeypatch.setitem(sys.modules, "imle.policies.unwritten", types.ModuleType("imle.policies.unwritten"))
    conditions.mkdir(exist_ok=True)
    (conditions.parent / "base.yaml").write_text((ROOT / "configs" / "base.yaml").read_text())
    config = conditions / "c9_unwritten.yaml"
    config.write_text("condition: C9\nmonitors: [unwritten]\n")
    return config


def test_conditions_without_a_policy_are_blocked(monkeypatch, tmp_path: Path):
    """A policy with no decide() blocks its condition; C1, C4 and C5 can all run."""
    conditions = ROOT / "configs" / "conditions"
    for name in ("c1_autonomous.yaml", "c4_divergence_prune.yaml", "c5_finding_correction.yaml"):
        assert launch_grid.blocked(conditions / name) is None
    assert "unwritten.decide is not implemented yet" in launch_grid.blocked(
        no_decide_policy(monkeypatch, tmp_path / "conditions"))


def test_status_and_dry_run(tmp_path: Path, monkeypatch, capsys):
    """--status counts finished runs as done; --dry-run lists only runs that still need running."""
    (tmp_path / "conditions").mkdir()
    (tmp_path / "conditions" / "c1_autonomous.yaml").write_text(
        (ROOT / "configs" / "conditions" / "c1_autonomous.yaml").read_text())
    no_decide_policy(monkeypatch, tmp_path / "conditions")
    (tmp_path / "base.yaml").write_text((ROOT / "configs" / "base.yaml").read_text())
    (tmp_path / "schedule.yaml").write_text(
        "defaults: {budget_hours: 1, runs_root: grid}\ntasks: [a, b]\n"
        "blocks: [{config: c1_autonomous.yaml, seeds: [0]}, {config: c9_unwritten.yaml, seeds: [0]}]\n")
    done = tmp_path / "grid" / "C1_a_seed0"
    checkpoint.write(done, 5, {"nodes": {}}, [], {"done": True})
    (done / "config.yaml").write_text("budget: {wall_clock_s: 3600}\n")
    monkeypatch.setattr(launch_grid, "ROOT", tmp_path)

    monkeypatch.setattr(sys, "argv", ["launch_grid.py", "--schedule", str(tmp_path / "schedule.yaml"), "--status"])
    launch_grid.main()
    assert "done: 1 · to do: 1 · blocked: 2" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["launch_grid.py", "--schedule", str(tmp_path / "schedule.yaml"), "--dry-run",
                                      "--sandbox", "subprocess"])
    launch_grid.main()
    out = capsys.readouterr().out
    assert "[1] C1_b_seed0" in out and "--sandbox subprocess" in out and "--budget-hours 1.0" in out
    assert "C1_a_seed0:" not in out and "skip C9_a_seed0: blocked" in out
