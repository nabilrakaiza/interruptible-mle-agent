import json
from pathlib import Path

from imle.apply import apply_pending
from imle.intervention import Action, Intervention, append
from imle.state import SearchState
from imle.tree import Node, NodeStatus, Operator, Tree


def make_tree() -> Tree:
    """n0 (working) -> n1 (working) -> n2 (buggy), plus a separate buggy draft n3."""
    t = Tree()
    t.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5, script_path="s"))
    t.add(Node(id="n1", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.6,
               script_path="s"))
    t.add(Node(id="n2", parent_id="n1", operator=Operator.IMPROVE, status=NodeStatus.BUGGY, script_path="s"))
    t.add(Node(id="n3", operator=Operator.DRAFT, status=NodeStatus.BUGGY, script_path="s"))
    return t


def queue(run_dir: Path, *items: tuple) -> None:
    """Append interventions given as (action, target, params) tuples, in timestamp order."""
    for i, (action, target, params) in enumerate(items):
        append(run_dir / "queue.jsonl", Intervention(
            id=f"q{i}", ts=f"2026-10-18T00:00:{i:02d}Z", source="human", action=action, target=target,
            params=params or {},
        ))


def outcomes(records) -> list[tuple[str, str | None]]:
    """(outcome, reason) per applied record."""
    return [(r.outcome, r.reason) for r in records]


def test_prune_marks_subtree_and_clears_dependent_state(tmp_path: Path):
    """Prune removes a whole subtree from selection and cancels a redirect or override inside it."""
    tree, state = make_tree(), SearchState(override_node="n1", forced_next={"operator": "improve", "parent_id": "n1"})
    queue(tmp_path, (Action.PRUNE, "n1", None), (Action.PRUNE, "n1", None), (Action.PRUNE, "n9", None))
    records = apply_pending(tmp_path, tree, [], state)
    assert outcomes(records) == [("applied", None), ("dropped", "already pruned"), ("dropped", "unknown node n9")]
    assert [n.status for n in tree.nodes.values()] == [
        NodeStatus.WORKING, NodeStatus.PRUNED, NodeStatus.PRUNED, NodeStatus.BUGGY,
    ]
    assert state.override_node is None and state.forced_next is None


def test_redirect_checks_the_operator_fits_the_target(tmp_path: Path):
    """Redirect to debug needs a buggy node, to improve a working one; draft needs no target."""
    tree, state = make_tree(), SearchState()
    queue(tmp_path,
          (Action.REDIRECT, "n0", {"operator": "debug"}),
          (Action.REDIRECT, "n3", {"operator": "improve"}),
          (Action.REDIRECT, "n0", {"operator": "explode"}),
          (Action.REDIRECT, "n3", {"operator": "debug"}))
    records = apply_pending(tmp_path, tree, [], state)
    assert [r.outcome for r in records] == ["dropped", "dropped", "dropped", "applied"]
    assert state.forced_next == {"operator": "debug", "parent_id": "n3"}
    queue_more = tmp_path / "more"
    queue_more.mkdir()
    queue(queue_more, (Action.REDIRECT, None, {"operator": "draft"}))
    apply_pending(queue_more, tree, [], state)
    assert state.forced_next == {"operator": "draft", "parent_id": None}


def test_override_inject_correct_rebudget_abandon(tmp_path: Path):
    """The remaining actions change the state they target, or are dropped with a reason."""
    tree, state = make_tree(), SearchState()
    findings = [{"id": "f1", "text": "old"}, {"id": "f2", "text": "wrong"}]
    queue(tmp_path,
          (Action.OVERRIDE, "n3", None),
          (Action.OVERRIDE, "n0", None),
          (Action.INJECT, None, {"card": "Try a char n-gram model."}),
          (Action.INJECT, None, {}),
          (Action.CORRECT, "f1", {"replacement": "new"}),
          (Action.CORRECT, "f2", None),
          (Action.CORRECT, "f9", None),
          (Action.REBUDGET, None, {"seconds": -600}),
          (Action.REBUDGET, None, {"seconds": "lots"}),
          (Action.ABANDON, "n2", None))
    records = apply_pending(tmp_path, tree, findings, state)
    assert [r.outcome for r in records] == [
        "dropped", "applied", "applied", "dropped", "applied", "applied", "dropped", "applied", "dropped", "dropped",
    ]
    assert state.override_node == "n0"
    assert state.injected_cards == [{"name": "injected approach", "summary": "Try a char n-gram model.", "source": "human"}]
    assert findings == [{"id": "f1", "text": "new", "corrected_by": "q4"}]
    assert state.extra_budget_s == -600


def test_each_item_is_handled_once_and_logged(tmp_path: Path):
    """Every outcome is written to applied.jsonl, and a handled item is not applied again."""
    tree, state = make_tree(), SearchState()
    queue(tmp_path, (Action.REBUDGET, None, {"seconds": 10}))
    apply_pending(tmp_path, tree, [], state)
    assert apply_pending(tmp_path, tree, [], state) == []
    logged = [json.loads(line) for line in (tmp_path / "applied.jsonl").read_text().splitlines()]
    assert len(logged) == 1 and logged[0]["outcome"] == "applied" and state.extra_budget_s == 10


def test_malformed_queue_does_not_crash(tmp_path: Path):
    """A bad line in queue.jsonl is reported and skipped instead of stopping the run."""
    (tmp_path / "queue.jsonl").write_text("{not json\n")
    assert apply_pending(tmp_path, make_tree(), [], SearchState()) == []
