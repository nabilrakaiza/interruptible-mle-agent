import importlib.util
import json
import sys
from pathlib import Path

import pytest

from imle import checkpoint
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trajectory", ROOT / "scripts" / "trajectory.py")
traj = importlib.util.module_from_spec(spec)
sys.modules["trajectory"] = traj  # dataclasses look their module up while it loads
spec.loader.exec_module(traj)

W, B = NodeStatus.WORKING, NodeStatus.BUGGY
D, DBG, IMP = Operator.DRAFT, Operator.DEBUG, Operator.IMPROVE
# id, operator, parent, status, val, probe, script, error
NODES = [
    ("n0", D, None, W, 0.50, 0.50, "LogisticRegression()", None),
    ("n1", IMP, "n0", W, 0.40, 0.45, "MLPClassifier()", None),                 # new best, uses the card
    ("n2", IMP, "n1", B, None, None, "x", "runtime_error: exit code 1"),
    ("n3", DBG, "n2", W, 0.30, 0.60, "MLPClassifier(alpha=1)", None),          # fixes n2; best val, poor probe
    ("n4", IMP, "n3", W, 0.35, 0.20, "RandomForestClassifier()", None),        # best on probe
]


def make_run(run_dir: Path, condition: str = "C4", final: str = "n3", interventions: bool = True) -> None:
    """A finished run with one crash and fix, a model card, and (optionally) a prune after n1."""
    tree = Tree(higher_is_better=False)
    for i, (nid, op, parent, status, val, probe, script, error) in enumerate(NODES):
        d = run_dir / "nodes" / nid
        (d / "output").mkdir(parents=True)
        (d / "solution.py").write_text(f"pd.read_csv('input/train.csv'); {script}")
        (d / "stderr.txt").write_text("Traceback\nKeyError: 'age'" if error else "")
        tree.add(Node(id=nid, operator=op, parent_id=parent, status=status, val_score=val, probe_score=probe,
                      error=error, plan=f"plan {nid}", script_path=f"nodes/{nid}/solution.py",
                      started_at=f"2026-10-19T10:0{i}:00+00:00", finished_at=f"2026-10-19T10:0{i}:30+00:00"))
    (run_dir / "config.yaml").write_text("search: {improve_min_rel_gain: 0.01, improve_patience: 3}\n")
    (run_dir / "model_cards.json").write_text(json.dumps({"cards": [
        {"name": "Multi-layer Perceptron Classifier", "modality": "tabular", "use_when": "w",
         "recipe": "Use MLPClassifier with alpha tuned.", "watch_out": "o", "source": "https://scikit-learn.org/"}]}))
    if interventions:
        record = {"intervention": {"id": "i1", "ts": "2026-10-19T10:01:40+00:00", "source": "divergence_prune",
                                   "action": "prune", "target": "n0", "params": {}, "note": "val and probe diverge"},
                  "outcome": "applied", "reason": None, "applied_at": "2026-10-19T10:01:45+00:00"}
        (run_dir / "applied.jsonl").write_text(json.dumps(record) + "\n")
    status = {"task": "toy", "seed": 0, "condition": condition, "done": True, "final_node": final,
              "final_selection": "best_val", "stop_reason": "max_nodes", "elapsed_s": 300}
    checkpoint.write(run_dir, 5, tree.model_dump(mode="json"), [], status)


def test_events_tell_the_story(tmp_path: Path):
    """Drafts, new bests, the crash and its fix, the card, the prune and the verdict all appear in order."""
    make_run(tmp_path / "run")
    evs = traj.events(traj.load(tmp_path / "run"))
    kinds = [(e.node, e.kind) for e in evs]
    assert kinds == [
        ("n0", "draft"), ("n0", "new best"),
        ("n1", "new best"), ("n1", "card used"), ("n1", "intervention"),
        ("n2", "crash"),
        ("n3", "fixed"), ("n3", "new best"),  # no overfitting label: its parent crashed, so has no val
        (None, "stop"), ("n3", "final pick"), ("n4", "best on probe"),
    ]
    notes = {k: e.note for e, k in zip(evs, kinds)}
    assert "MLPClassifier" in notes[("n1", "card used")]
    assert notes[("n1", "intervention")] == "divergence_prune: prune n0, applied - val and probe diverge"
    assert notes[("n2", "crash")] == "runtime_error: KeyError: 'age'"
    assert "after 1 attempt(s)" in notes[("n3", "fixed")]
    assert notes[("n3", "final pick")] == "val 0.3000 (rank 1 of 4), probe 0.6000 (rank 4 of 4)"
    assert "val rank 2 of 4" in notes[("n4", "best on probe")]


def test_crash_note_names_the_category_once(tmp_path: Path):
    """A crash without a traceback shows its error once, not as 'runtime_error: runtime_error: ...'."""
    make_run(tmp_path / "run")
    (tmp_path / "run" / "nodes" / "n2" / "stderr.txt").write_text("")
    evs = traj.events(traj.load(tmp_path / "run"))
    crash = next(e for e in evs if e.kind == "crash")
    assert crash.note == "runtime_error: exit code 1"


def test_timeline_and_figure_are_written(tmp_path: Path, monkeypatch, capsys):
    """The command writes timeline.md and trajectory.png into the run's trajectory folder."""
    pytest.importorskip("matplotlib")
    make_run(tmp_path / "run")
    monkeypatch.setattr(sys, "argv", ["trajectory.py", str(tmp_path / "run")])
    traj.main()
    out = tmp_path / "run" / "trajectory"
    assert (out / "trajectory.png").stat().st_size > 10_000
    md = (out / "timeline.md").read_text()
    assert "- **Interventions** 1 applied, 0 dropped" in md and "| n3 | final pick |" in md
    assert "## Annotations" in capsys.readouterr().out


def test_pairs_compare_with_the_c1_twin(tmp_path: Path):
    """An intervened run is compared with the C1 run of the same task and seed on its final check score."""
    make_run(tmp_path / "runs" / "c4_run", condition="C4", final="n4")
    make_run(tmp_path / "runs" / "c1_run", condition="C1", final="n3", interventions=False)
    table = traj.pairs([tmp_path / "runs"])
    row = next(line for line in table.splitlines() if line.startswith("| c4_run"))
    assert "| 0.2000 (probe) | 0.6000 | -0.4000 | helped |" in row
    assert "c1_run |" not in table  # C1 runs without interventions are the baseline, not candidates
    assert "No intervened run" in traj.pairs([tmp_path / "runs" / "c1_run"])
