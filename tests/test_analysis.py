"""Stage 7: the validation-test gap and probe fidelity analyses, on fake runs written with checkpoint.write."""

import importlib.util
import math
from pathlib import Path

import pandas as pd
import pytest

from imle import checkpoint
from imle.metrics import bootstrap_ci, spearman, top_k_agreement
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gap = load("analyze_val_test_gap")
fidelity = load("analyze_probe_fidelity")

W, B = NodeStatus.WORKING, NodeStatus.BUGGY


def write_run(runs: Path, name: str, condition: str, task: str, seed: int, higher_is_better: bool,
              nodes: list[tuple], final: str | None = None) -> None:
    """nodes: (id, parent, status, val, probe, test). Earlier checkpoints are written too, and must be ignored."""
    tree = Tree(higher_is_better=higher_is_better)
    for node_id, parent, status, val, probe, test in nodes:
        tree.add(Node(id=node_id, parent_id=parent, operator=Operator.IMPROVE if parent else Operator.DRAFT,
                      status=status, val_score=val, probe_score=probe, test_score=test))
    status = {"condition": condition, "task": task, "seed": seed, "done": True}
    if final:
        status["final_node"] = final
    checkpoint.write(runs / name, 0, Tree().model_dump(mode="json"), [], {"condition": condition})
    checkpoint.write(runs / name, 1, tree.model_dump(mode="json"), [], status)


@pytest.fixture
def runs(tmp_path: Path) -> Path:
    root = tmp_path / "runs"
    write_run(root, "c1_spooky_s0", "C1", "spooky", 0, False, [
        ("n0", None, W, 0.50, 0.52, 0.55),
        ("n1", "n0", W, 0.40, 0.45, 0.48),
        ("n2", "n0", W, 0.35, 0.50, 0.50),
        ("n3", "n0", B, None, None, None),
        ("n4", None, W, 0.60, 0.61, None),       # no test score: skipped and counted
    ], final="n2")
    write_run(root, "c1_spooky_s1", "C1", "spooky", 1, False, [("n0", None, W, 0.50, 0.50, 0.52)])
    write_run(root, "c5_insults_s0", "C5", "insults", 0, True, [("n0", None, W, 0.90, 0.85, 0.80)])
    (root / "not_a_run").mkdir()
    (root / "half_written" / "checkpoints" / "000000").mkdir(parents=True)   # no status.json
    return root


def test_val_test_gap(runs: Path, tmp_path: Path):
    nodes, per_run, summary = gap.main(["--runs-dir", str(runs), "--out", str(tmp_path / "gap")])
    s0_nodes = nodes[nodes["run"] == "c1_spooky_s0"].set_index("node_id")["gap"]
    assert s0_nodes.to_dict() == pytest.approx({"n0": 0.05, "n1": 0.08, "n2": 0.15})
    s0 = per_run.set_index("run").loc["c1_spooky_s0"]
    assert s0["final_gap"] == pytest.approx(0.15) and s0["best_val_gap"] == pytest.approx(0.15)
    assert s0["mean_gap"] == pytest.approx((0.05 + 0.08 + 0.15) / 3)
    assert s0["nodes_with_test"] == 3 and s0["working_without_test"] == 1
    assert per_run.set_index("run").loc["c1_spooky_s1", "final_gap"] == pytest.approx(0.02)  # best-val stands in
    assert per_run.set_index("run").loc["c5_insults_s0", "final_gap"] == pytest.approx(0.10)  # higher is better
    c1 = summary.set_index(["condition", "task"]).loc[("C1", "spooky")]
    assert c1["final_gap_mean"] == pytest.approx(0.085) and c1["final_gap_n"] == 2
    assert c1["final_gap_sd"] == pytest.approx(math.sqrt(2) * 0.065)
    assert 0.02 - 1e-12 <= c1["final_gap_ci_low"] <= c1["final_gap_ci_high"] <= 0.15 + 1e-12
    assert sorted(per_run["run"]) == ["c1_spooky_s0", "c1_spooky_s1", "c5_insults_s0"]
    assert {"nodes.csv", "runs.csv", "summary.csv"} <= {p.name for p in (tmp_path / "gap").iterdir()}


def test_probe_fidelity(runs: Path, tmp_path: Path):
    per_run, summary = fidelity.main(["--runs-dir", str(runs), "--k", "1", "--out", str(tmp_path / "pf")])
    s0 = per_run.set_index("run").loc["c1_spooky_s0"]
    assert s0["nodes"] == 3 and s0["spearman"] == pytest.approx(1.0) and s0["top_k"] == 1.0
    assert s0["val_spearman"] == pytest.approx(0.5) and s0["val_top_k"] == 0.0
    assert math.isnan(per_run.set_index("run").loc["c1_spooky_s1", "spearman"])  # one node
    assert set(summary["condition"]) == {"C1", "C5"}


def test_glob_and_condition_key(runs: Path, tmp_path: Path):
    per_run, _ = fidelity.main(["--runs-dir", str(runs), "--glob", "c5_*", "--out", str(tmp_path / "pf")])
    assert list(per_run["run"]) == ["c5_insults_s0"]
    _, per_run, _ = gap.main(["--runs-dir", str(runs), "--condition-key", "task", "--out", str(tmp_path / "g")])
    assert set(per_run["condition"]) == {"spooky", "insults"}


def test_outputs_are_deterministic(runs: Path, tmp_path: Path):
    gap.main(["--runs-dir", str(runs), "--out", str(tmp_path / "a")])
    gap.main(["--runs-dir", str(runs), "--out", str(tmp_path / "b")])
    assert (tmp_path / "a" / "summary.csv").read_text() == (tmp_path / "b" / "summary.csv").read_text()


def test_helpers():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert spearman([1, 2, 2, 3], [1, 2, 3, 4]) == pytest.approx(pd.Series([1, 2, 2, 3]).corr(
        pd.Series([1, 2, 3, 4]), method="spearman"))
    assert math.isnan(spearman([1, 1, 1], [1, 2, 3]))
    assert top_k_agreement([0.9, 0.8, 0.1], [0.1, 0.8, 0.9], 1, higher_is_better=True) == 0.0
    assert top_k_agreement([0.9, 0.8, 0.1], [0.1, 0.8, 0.9], 1, higher_is_better=False) == 0.0
    assert top_k_agreement([3, 2, 1], [3, 1, 2], 2, higher_is_better=True) == 0.5
    assert top_k_agreement([1, 2], [1, 2], 10, higher_is_better=True) == 1.0
    assert bootstrap_ci([2.0, 2.0, 2.0]) == (2.0, 2.0)
    assert all(math.isnan(x) for x in bootstrap_ci([float("nan")]))
