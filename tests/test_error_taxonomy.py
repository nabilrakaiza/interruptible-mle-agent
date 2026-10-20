import importlib.util
import sys
from pathlib import Path

import pytest

from imle import checkpoint
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("error_taxonomy", ROOT / "scripts" / "error_taxonomy.py")
tax = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tax)

W, B = NodeStatus.WORKING, NodeStatus.BUGGY
D, DBG, IMP = Operator.DRAFT, Operator.DEBUG, Operator.IMPROVE
# id, operator, parent, status, val, probe, error, stderr, predictions, script mentions extra.csv
NODES = [
    ("n0", D, None, W, 0.5, 0.5, None, "", "0.1,0.2", True),
    ("n1", IMP, "n0", W, 0.4, 0.6, None, "", "0.3,0.4", True),         # better val, worse probe
    ("n2", IMP, "n1", W, 0.4, 0.6, None, "", "0.3,0.4", True),         # same predictions as n1
    ("n3", IMP, "n1", B, None, None, "runtime_error: exit code 1", "Traceback ...\nKeyError: 'age'", None, True),
    ("n4", DBG, "n3", B, None, None, "runtime_error: exit code 1",
     "ValueError: X has 3 features, but StandardScaler is expecting 4 features as input.", None, True),
    ("n5", DBG, "n4", W, 0.45, 0.5, None, "", "0.2,0.2", False),       # fixed on the 2nd attempt
    ("n6", D, None, B, None, None, "timeout: killed after 10s", "", None, True),
    ("n7", D, None, B, None, None, "invalid_submission: wrong columns", "", None, True),
    ("n8", D, None, B, None, None, "generation_error: empty reply", "", None, True),
]


def make_run(run_dir: Path, nodes: list[tuple] = NODES) -> None:
    """A finished C1 run with one node of every kind, written the way the controller writes it."""
    tree = Tree(higher_is_better=False)
    (run_dir / "workspace" / "input").mkdir(parents=True)
    for name in ("train.csv", "predict.csv", "extra.csv"):
        (run_dir / "workspace" / "input" / name).write_text("id\n1\n")
    for nid, op, parent, status, val, probe, error, stderr, preds, uses_extra in nodes:
        d = run_dir / "nodes" / nid
        (d / "output").mkdir(parents=True)
        script = "pd.read_csv('input/train.csv'); pd.read_csv('input/predict.csv')"
        (d / "solution.py").write_text(script + ("; pd.read_csv('input/extra.csv')" if uses_extra else ""))
        (d / "stderr.txt").write_text(stderr)
        if preds:
            a, b = preds.split(",")
            (d / "output" / "predictions.csv").write_text(f"id,y\n1,{a}\n2,{b}\n")
        tree.add(Node(id=nid, operator=op, parent_id=parent, status=status, val_score=val, probe_score=probe,
                      error=error, plan=f"plan {nid}", script_path=f"nodes/{nid}/solution.py"))
    (run_dir / "config.yaml").write_text("search: {improve_min_rel_gain: 0.01}\n")
    status = {"task": "toy", "seed": 0, "condition": "C1", "done": True, "final_node": "n1",
              "stop_reason": "max_nodes"}
    checkpoint.write(run_dir, 9, tree.model_dump(mode="json"), [], status)


def test_runtime_subtypes():
    """The last exception line of stderr decides the subtype."""
    assert tax.runtime_subtype("Traceback\n  File x\nModuleNotFoundError: No module named 'lightgbm'")[0] == \
        "import_error"
    assert tax.runtime_subtype("ValueError: could not convert string to float: 'a'")[0] == "value_error"
    assert tax.runtime_subtype("ValueError: Found input variables with inconsistent numbers of samples")[0] == \
        "shape_mismatch"
    assert tax.runtime_subtype("sklearn.exceptions.NotFittedError: not fitted")[0] == "other"
    assert tax.runtime_subtype("Killed") == ("other", "")


def test_killed_scripts_are_out_of_memory(tmp_path: Path):
    """A script killed without a timeout and without a Python exception gets the out_of_memory subtype."""
    assert tax.killed("runtime_error: exit code 137 (killed, most likely out of memory: the limit is 4 GB)\n")
    assert tax.killed("runtime_error: exit code -9 (killed)")
    assert not tax.killed("runtime_error: exit code 1\nKeyError: 'a'")
    assert not tax.killed("runtime_error: exit code 1370") and not tax.killed(None)

    killed = ("n3", IMP, "n1", B, None, None, "runtime_error: exit code 137 (killed, most likely out of memory)",
              "", None, True)
    run_dir = tmp_path / "run"
    make_run(run_dir, [killed if n[0] == "n3" else n for n in NODES])
    rows, _ = tax.classify_run(run_dir)
    assert {r["node"]: r for r in rows}["n3"]["subtype"] == "out_of_memory"


def test_classify_run(tmp_path: Path):
    """Every category, label and run-level number comes out as designed on a hand-built run."""
    run_dir = tmp_path / "runs" / "c1_toy_seed0"
    make_run(run_dir)
    (tmp_path / "runs" / "_analysis").mkdir()  # not a run: no checkpoints
    assert tax.find_runs([tmp_path / "runs"]) == [run_dir]

    rows, summary = tax.classify_run(run_dir)
    by_id = {r["node"]: r for r in rows}
    assert [by_id[n]["category"] for n in ("n0", "n3", "n6", "n7", "n8")] == [
        "working", "runtime_error", "timeout", "invalid_submission", "generation_error"]
    assert by_id["n3"]["subtype"] == "missing_key_or_column" and by_id["n4"]["subtype"] == "shape_mismatch"
    assert by_id["n1"]["labels"] == "validation_overfitting"
    assert by_id["n2"]["labels"] == "no_gain,no_change"
    assert by_id["n5"]["labels"] == "unused_data:extra.csv"
    assert by_id["n0"]["labels"] == ""

    assert summary["failures_debugged"] == 1 and summary["debug_chains_fixed"] == 1
    assert summary["mean_attempts_to_fix"] == 2
    assert summary["longest_no_new_best"] == 7 and summary["nodes_after_final_best"] == 7
    assert summary["selection_regret"] == pytest.approx(0.1) and summary["regret_basis"] == "probe"
    assert summary["working_rate"] == round(4 / 9, 3)


def test_test_scores_take_over_from_probe(tmp_path: Path):
    """Once nodes are graded, overfitting and regret are judged on test instead of probe."""
    run_dir = tmp_path / "run"
    make_run(run_dir)
    ck = checkpoint.read(run_dir)
    for nid, test in [("n0", 0.5), ("n1", 0.45), ("n2", 0.45), ("n5", 0.3)]:
        ck["tree"]["nodes"][nid]["test_score"] = test
    checkpoint.write(run_dir, 10, ck["tree"], [], ck["status"])

    rows, summary = tax.classify_run(run_dir)
    assert {r["node"]: r for r in rows}["n1"]["labels"] == ""  # test improved with validation
    assert summary["regret_basis"] == "test" and summary["selection_regret"] == pytest.approx(0.15)


def test_main_writes_the_tables(tmp_path: Path, monkeypatch, capsys):
    """The command writes nodes.csv, runs.csv and summary.md, and prints the summary."""
    make_run(tmp_path / "runs" / "r1")
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["error_taxonomy.py", str(tmp_path / "runs"), "--out", str(out)])
    tax.main()
    assert {p.name for p in out.iterdir()} == {"nodes.csv", "runs.csv", "summary.md"}
    printed = capsys.readouterr().out
    assert "1 runs, 9 nodes." in printed and "| missing_key_or_column | 1 |" in printed
