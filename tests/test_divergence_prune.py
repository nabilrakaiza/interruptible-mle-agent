
from pathlib import Path

from imle.tree import Node, Tree, NodeStatus, Operator
from imle.policies.divergence_prune import decide

from datetime import datetime, timezone

from imle.apply import apply_pending
from imle.intervention import Intervention, append
from imle.state import SearchState


def make_checkpoint(parent_val, parent_probe,
                    child_val, child_probe,
                    higher_is_better=True):

    tree = Tree(higher_is_better=higher_is_better)

    parent = Node(
        id="n1",
        operator=Operator.DRAFT,
        status=NodeStatus.WORKING,
        val_score=parent_val,
        probe_score=parent_probe,
    )

    child = Node(
        id="n2",
        parent_id="n1",
        operator=Operator.IMPROVE,
        status=NodeStatus.WORKING,
        val_score=child_val,
        probe_score=child_probe,
    )

    tree.add(parent)
    tree.add(child)

    return {
        "step": 2,
        "tree": tree.model_dump(mode="json"),
        "findings": [],
        "status": {
            "current_node": "n2",
        },
    }

def test_clear_divergence():
    ck = make_checkpoint(0.80, 0.79, 0.92, 0.75)

    actions = decide(Path("test_run"), ck)

    assert len(actions) == 1
    assert actions[0]["action"] == "prune"
    assert actions[0]["target"] == "n2"


def test_both_scores_improve():
    ck = make_checkpoint(0.80, 0.79, 0.86, 0.84)

    assert decide(Path("test_run"), ck) == []


def test_small_probe_drop():
    ck = make_checkpoint(0.80, 0.79, 0.88, 0.785)

    assert decide(Path("test_run"), ck) == []


def test_validation_worsens():
    ck = make_checkpoint(0.80, 0.79, 0.77, 0.73)

    assert decide(Path("test_run"), ck) == []


def test_lower_is_better():
    ck = make_checkpoint(
        0.50, 0.52,
        0.40, 0.61,
        higher_is_better=False,
    )

    actions = decide(Path("test_run"), ck)

    assert len(actions) == 1
    assert actions[0]["target"] == "n2"


def test_missing_probe_score():
    ck = make_checkpoint(0.80, 0.79, 0.92, None)

    assert decide(Path("test_run"), ck) == []


def test_already_pruned():
    ck = make_checkpoint(0.80, 0.79, 0.92, 0.75)
    ck["tree"]["nodes"]["n2"]["status"] = "pruned"

    assert decide(Path("test_run"), ck) == []


def test_test_score_is_ignored():
    ck = make_checkpoint(0.80, 0.79, 0.92, 0.75)
    ck["tree"]["nodes"]["n2"]["test_score"] = 0.99

    actions = decide(Path("test_run"), ck)

    assert len(actions) == 1
    assert actions[0]["target"] == "n2"

def test_no_duplicate_after_pruning():
    ck = make_checkpoint(0.80, 0.79, 0.92, 0.75)

    # First safe point: pruning should be requested.
    first_actions = decide(Path("test_run"), ck)

    assert len(first_actions) == 1

    # Simulate A5 applying the prune intervention.
    ck["tree"]["nodes"]["n2"]["status"] = "pruned"

    # Next safe point: no new prune request.
    second_actions = decide(Path("test_run"), ck)

    assert second_actions == []


def test_pruning_integration(tmp_path):
    # Create a checkpoint with clear divergence.
    ck = make_checkpoint(0.80, 0.79, 0.92, 0.75)

    # Reconstruct the actual tree.
    tree = Tree.model_validate(ck["tree"])

    # Ask our C4 policy for interventions.
    actions = decide(tmp_path, ck)

    assert len(actions) == 1

    # Simulate the controller adding metadata and queuing.
    for i, action in enumerate(actions):
        item = Intervention.model_validate({
            **action,
            "id": f"divergence_prune-s2-{i}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "divergence_prune",
        })

        append(tmp_path / "queue.jsonl", item)

    # Simulate A5 processing the intervention queue.
    state = SearchState()
    records = apply_pending(tmp_path, tree, [], state)

    # Verify the intervention was applied.
    assert len(records) == 1
    assert records[0].outcome == "applied"

    # Verify the target was actually pruned.
    assert tree.nodes["n2"].status == NodeStatus.PRUNED

    # Verify it is no longer selectable.
    assert "n2" not in [n.id for n in tree.selectable()]

    # Repeated processing should not reapply the action.
    assert apply_pending(tmp_path, tree, [], state) == []


def test_no_current_node():
    ck = make_checkpoint(0.80, 0.79, 0.92, 0.75)

    # No newly completed node to inspect.
    ck["status"]["current_node"] = None

    assert decide(Path("test_run"), ck) == []

