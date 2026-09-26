from pathlib import Path

import pytest

from imle import checkpoint
from imle.intervention import Action, Intervention, append, pending
from imle.tree import Node, NodeStatus, Operator, Tree


def test_tree_add_and_best():
    t = Tree()
    t.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.7))
    t.add(Node(id="n1", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.8))
    t.add(Node(id="n2", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.BUGGY))
    assert t.best_by_val().id == "n1"
    assert set(t.subtree_ids("n0")) == {"n0", "n1", "n2"}


def test_tree_rejects_unknown_parent():
    with pytest.raises(ValueError):
        Tree().add(Node(id="n1", parent_id="missing", operator=Operator.DRAFT))


def test_queue_pending(tmp_path: Path):
    q, applied = tmp_path / "queue.jsonl", tmp_path / "applied.jsonl"
    append(q, Intervention(id="q1", ts="2026-10-01T00:00:02Z", source="human", action=Action.PRUNE, target="n3"))
    append(q, Intervention(id="q2", ts="2026-10-01T00:00:01Z", source="human", action=Action.REDIRECT, target="n1"))
    ids = [i.id for i in pending(q, applied)]
    assert ids == ["q2", "q1"]  # timestamp order


def test_checkpoint_roundtrip(tmp_path: Path):
    checkpoint.write(tmp_path, 1, {"nodes": {}}, [], {"current_node": None})
    checkpoint.write(tmp_path, 2, {"nodes": {"n0": {}}}, [], {"current_node": "n0"})
    ck = checkpoint.read(tmp_path)
    assert ck["step"] == 2 and ck["status"]["current_node"] == "n0"
