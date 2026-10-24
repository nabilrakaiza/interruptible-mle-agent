"""Stage 6: the leakage stress test and the finding-accuracy check."""

import importlib.util
from pathlib import Path

import pandas as pd

from imle import checkpoint
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stress = load("leakage_stress_test", ROOT / "scripts" / "leakage_stress_test.py")
accuracy = load("finding_accuracy", ROOT / "scripts" / "finding_accuracy.py")
make_data = load("make_data", ROOT / "scripts" / "leakage" / "make_data.py")


# --------------------------------------------------------------------------- leakage stress test


def test_every_leak_type_has_a_planted_script_and_a_clean_control():
    items = stress.fixtures()
    pairs = {(kind, leak) for _, kind, leak in items}
    assert pairs == {(k, t) for k in ("planted", "clean") for t in stress.EXPECTED_RULE}


def test_stress_test_detects_planted_and_passes_clean(tmp_path: Path):
    rows = stress.main(["--out", str(tmp_path / "leakage_stress.csv")])
    assert rows[rows.kind == "planted"]["expected_rule_hit"].all()
    assert not rows[rows.kind == "clean"]["flagged"].any()
    summary = pd.read_csv(tmp_path / "leakage_stress_summary.csv")
    fp = summary[summary.measure == "false_positive_rate"]["rate"].item()
    assert fp == 0 and (summary[summary.measure == "detection_rate"]["rate"] == 1).all()


def test_fixtures_run_on_synthetic_data(tmp_path: Path):
    rows = stress.main(["--out", str(tmp_path / "s.csv"), "--execute", "--work-dir", str(tmp_path / "work")])
    assert rows["ran"].all()


def test_real_scripts_are_screened_without_ground_truth(tmp_path: Path):
    (tmp_path / "a.py").write_text("import pandas as pd\nx = pd.read_csv('../stand_in/harness/labels.csv')\n")
    (tmp_path / "b.py").write_text("print('fine')\n")
    stress.main(["--out", str(tmp_path / "s.csv"), "--scripts", str(tmp_path / "*.py")])
    summary = pd.read_csv(tmp_path / "s_summary.csv").set_index("measure")
    assert summary.loc["real_script_flag_rate", "rate"] == 0.5 and summary.loc["real_script_leak_rate", "n"] == 2


def test_synthetic_data_is_deterministic(tmp_path: Path):
    a, b = make_data.make(tmp_path / "a", seed=1), make_data.make(tmp_path / "b", seed=1)
    for name in ("train.csv", "predict.csv"):
        assert (a / name).read_text() == (b / name).read_text()
    assert "outcome" not in pd.read_csv(a / "predict.csv").columns


# --------------------------------------------------------------------------- finding accuracy


def tree() -> Tree:
    """Lower is better. n0, n1 drafts; n2 improves n0 on val and probe; n3 improves val only; n4 buggy."""
    t = Tree(higher_is_better=False)
    W = NodeStatus.WORKING
    t.add(Node(id="n0", operator=Operator.DRAFT, status=W, val_score=0.50, probe_score=0.50))
    t.add(Node(id="n1", operator=Operator.DRAFT, status=W, val_score=0.60, probe_score=0.60))
    t.add(Node(id="n2", parent_id="n0", operator=Operator.IMPROVE, status=W, val_score=0.40, probe_score=0.45))
    t.add(Node(id="n3", parent_id="n0", operator=Operator.IMPROVE, status=W, val_score=0.45, probe_score=0.55))
    t.add(Node(id="n4", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.BUGGY))
    return t


def f(fid: str, effect: str, *cited: tuple[str, float | None]) -> dict:
    return {"id": fid, "text": fid, "effect": effect,
            "evidence": [{"node_id": n, "val_score": v} for n, v in cited]}


CASES = {
    "f-helps": (f("f-helps", "helps", ("n2", 0.40)), True, True),
    "f-val-only": (f("f-val-only", "helps", ("n3", 0.45)), True, False),
    "f-wrong-direction": (f("f-wrong-direction", "hurts", ("n2", 0.40)), False, False),
    "f-missing": (f("f-missing", "helps", ("n9", 0.1)), False, False),
    "f-misquoted": (f("f-misquoted", "helps", ("n2", 0.35)), False, False),
    "f-crash": (f("f-crash", "hurts", ("n4", None)), True, True),
    "f-draft": (f("f-draft", "helps", ("n0", 0.50)), True, True),     # beats the median of the other drafts
    "f-neutral": (f("f-neutral", "neutral", ("n1", 0.60)), True, True),
    "f-empty": ({"id": "f-empty", "text": "x", "effect": "helps", "evidence": []}, False, False),
}


def test_each_definition_case():
    t = tree()
    for fid, (finding, supported, replicated) in CASES.items():
        result = accuracy.check(finding, t)
        assert (result["supported"], result["replicated"]) == (supported, replicated), (fid, result)


def test_run_level_fractions_from_checkpoints(tmp_path: Path):
    run = tmp_path / "C1_spooky_seed0"
    t = tree().model_dump(mode="json")
    first = [CASES["f-helps"][0], CASES["f-missing"][0]]
    checkpoint.write(run, 0, t, [], {})
    checkpoint.write(run, 1, t, first, {})
    checkpoint.write(run, 2, t, first[:1] + [CASES["f-val-only"][0]], {})   # f-missing deleted, one added
    findings, runs = accuracy.main([str(run), "--out", str(tmp_path / "fa.csv")])
    assert list(findings["finding_id"]) == ["f-helps", "f-missing", "f-val-only"]
    assert list(findings["step"]) == [1, 1, 2]
    row = runs.iloc[0]
    assert row["findings"] == 3 and abs(row["unsupported_fraction"] - 1 / 3) < 1e-12
    assert abs(row["replicated_fraction"] - 1 / 3) < 1e-12
    assert (tmp_path / "fa_runs.csv").exists()
