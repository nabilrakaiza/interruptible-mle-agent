import json
from pathlib import Path

import pandas as pd

from imle import checkpoint, monitor
from imle.apply import apply_pending
from imle.intervention import Action
from imle.state import SearchState
from imle.tree import Node, NodeStatus, Operator, Tree


def make_run(run_dir: Path) -> Tree:
    """n0 (draft) -> n1 (improve, better val, worse probe), n2 buggy draft; lower is better. Two checkpoints."""
    tree = Tree(higher_is_better=False)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5, probe_score=0.5,
                  test_score=0.52, plan="logistic regression", finished_at="2026-10-24T00:01:00+00:00"))
    checkpoint.write(run_dir, 1, tree.model_dump(mode="json"), [], {"current_node": "n0"})
    tree.add(Node(id="n1", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.4,
                  probe_score=0.6, test_score=0.61, finished_at="2026-10-24T00:02:00+00:00"))
    tree.add(Node(id="n2", operator=Operator.DRAFT, status=NodeStatus.BUGGY, error="runtime_error: exit code 1",
                  finished_at="2026-10-24T00:03:00+00:00"))
    checkpoint.write(run_dir, 2, tree.model_dump(mode="json"), [], {"current_node": "n2", "done": True})
    (run_dir / "nodes" / "n1").mkdir(parents=True)
    (run_dir / "nodes" / "n1" / "solution.py").write_text("print('hi')\n")
    (run_dir / "nodes" / "n1" / "stdout.txt").write_text("x" * 5000 + "END")
    return tree


def test_find_runs_looks_into_nested_folders(tmp_path: Path):
    """Runs one or two levels down are found; folders starting with _ (analysis output) are not."""
    for name in ("a/run1", "run2", "_analysis/run3"):
        (tmp_path / name / "checkpoints").mkdir(parents=True)
    assert [p.relative_to(tmp_path).as_posix() for p in monitor.find_runs(tmp_path)] == ["a/run1", "run2"]
    assert monitor.find_runs(tmp_path / "missing") == []


def test_node_frame_hides_test_scores_by_default(tmp_path: Path):
    """Monitors never see test scores unless asked for a finished run's analysis."""
    make_run(tmp_path)
    ck = monitor.read_step(tmp_path)
    assert monitor.complete_steps(tmp_path) == [1, 2] and ck["step"] == 2
    nodes = monitor.node_frame(ck)
    assert "test_score" not in nodes and nodes["order"].tolist() == [0, 1, 2]
    assert "test_score" in monitor.node_frame(ck, show_test=True)
    assert len(monitor.node_frame(monitor.read_step(tmp_path, 1))) == 1


def test_best_so_far_follows_validation(tmp_path: Path):
    """The best-by-validation node after each node, skipping buggy ones; its probe is what C4 watches."""
    make_run(tmp_path)
    best = monitor.best_so_far(monitor.node_frame(monitor.read_step(tmp_path)), higher_is_better=False)
    assert best["best_node"].tolist() == ["n0", "n1", "n1"]
    assert best["probe_score"].tolist() == [0.5, 0.6, 0.6]
    long = monitor.long_scores(best)
    assert set(long["split"]) == {"validation", "probe"} and len(long) == 6


def test_tree_dot_draws_every_edge_and_marks_the_final_node(tmp_path: Path):
    """One DOT node per tree node, one edge per parent link, the final node starred."""
    make_run(tmp_path)
    dot = monitor.tree_dot(monitor.node_frame(monitor.read_step(tmp_path)), final="n1")
    assert dot.count("->") == 1 and '"n0" -> "n1"' in dot and "n1 improve ★" in dot
    assert "val 0.4 | probe 0.6" in dot and "#c62828" in dot  # n2 is red (buggy)


def test_queue_history_and_positions(tmp_path: Path):
    """Queued items show as pending, then applied or dropped once the agent handles them, placed on the node axis."""
    tree = make_run(tmp_path)
    monitor.queue_intervention(tmp_path, Action.PRUNE, "n1", note="val up, probe down", session="s1")
    monitor.queue_intervention(tmp_path, "override", "n9", session="s1")
    assert monitor.history(tmp_path)["outcome"].tolist() == ["pending", "pending"]
    apply_pending(tmp_path, tree, [], SearchState())
    hist = monitor.history(tmp_path)
    assert hist["outcome"].tolist() == ["applied", "dropped"] and hist["reason"].iloc[1] == "unknown node n9"
    marks = monitor.intervention_positions(hist, monitor.node_frame(monitor.read_step(tmp_path)))
    assert marks["order"].tolist() == [2.5]  # after all three nodes finished
    log = [json.loads(line) for line in (tmp_path / monitor.LOG_NAME).read_text().splitlines()]
    assert [(e["event"], e["action"], e["target"]) for e in log] == [("queue", "prune", "n1"),
                                                                     ("queue", "override", "n9")]


def test_history_is_empty_without_a_queue(tmp_path: Path):
    """A run nobody intervened on has an empty history with the usual columns."""
    hist = monitor.history(tmp_path)
    assert hist.empty and "outcome" in hist
    assert monitor.intervention_positions(hist, pd.DataFrame()).empty


def test_node_files_tails_long_output(tmp_path: Path):
    """The script in full, stdout cut to its end, missing files as empty strings."""
    make_run(tmp_path)
    files = monitor.node_files(tmp_path, "n1", tail_chars=10)
    assert files["script"] == "print('hi')\n" and files["stdout"].endswith("END") and len(files["stdout"]) == 10
    assert files["stderr"] == "" and monitor.node_files(tmp_path, "n0")["script"] == ""


def test_dashboard_renders_a_run(tmp_path: Path, monkeypatch):
    """The page renders in live and replay mode; it logs a running run for C6 and leaves a finished one alone."""
    from streamlit.testing.v1 import AppTest

    run = tmp_path / "runs" / "r1"
    make_run(run)
    monkeypatch.chdir(tmp_path)
    app = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    at = AppTest.from_file(str(app), default_timeout=30).run()
    assert not at.exception, at.exception
    assert any("Best validation" in m.label for m in at.metric)
    at.sidebar.radio[0].set_value("Replay").run()
    assert not at.exception, at.exception
    assert not (run / monitor.LOG_NAME).exists()  # finished run

    status = run / "checkpoints" / "000002" / "status.json"
    status.write_text(json.dumps({"current_node": "n2", "done": False}))
    at = AppTest.from_file(str(app), default_timeout=30).run()
    assert not at.exception, at.exception
    events = [json.loads(line)["event"] for line in (run / monitor.LOG_NAME).read_text().splitlines()]
    assert events == ["session_start", "view_node"]


def test_score_range_ignores_outliers():
    """A single huge score does not stretch the axis; the best-so-far lines always fit."""
    points = pd.Series([0.30, 0.31, 0.32, 0.33] * 25 + [30.0])
    lo, hi = monitor.score_range(points, pd.Series([0.29, 0.30]))
    assert lo < 0.29 and 0.33 <= hi < 1
    assert monitor.score_range(pd.Series(dtype=float), pd.Series(dtype=float)) is None
    assert monitor.score_range(pd.Series([0.5]), pd.Series([0.5])) == [0.475, 0.525]


def test_last_update_is_zero_without_checkpoints(tmp_path: Path):
    """A run folder with no complete checkpoint sorts as oldest."""
    assert monitor.last_update(tmp_path) == 0.0
    make_run(tmp_path)
    assert monitor.last_update(tmp_path) > 0
