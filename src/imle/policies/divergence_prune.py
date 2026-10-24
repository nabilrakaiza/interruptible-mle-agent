
"""C4: Scripted divergence-pruning intervention policy."""

from pathlib import Path

from imle.tree import Tree, NodeStatus


MIN_VAL_GAIN = 0.02
MIN_PROBE_DROP = 0.02


def has_divergence(parent, child, higher_is_better=True):
    """Detect validation improvement with probe deterioration."""

    scores = [
        parent.val_score,
        parent.probe_score,
        child.val_score,
        child.probe_score,
    ]

    if any(score is None for score in scores):
        return False

    direction = 1 if higher_is_better else -1

    val_gain = direction * (
        child.val_score - parent.val_score
    )

    probe_gain = direction * (
        child.probe_score - parent.probe_score
    )

    return (
        val_gain > MIN_VAL_GAIN
        and probe_gain < -MIN_PROBE_DROP
    )



def decide(run_dir: Path, ck: dict) -> list[dict]:
    """Evaluate the current node for validation-probe divergence."""

    if ck is None:
        return []

    tree = Tree.model_validate(ck["tree"])

    current_id = ck.get("status", {}).get("current_node")

    if current_id is None:
        return []

    node = tree.nodes.get(current_id)

    if node is None or node.status != NodeStatus.WORKING:
        return []

    if node.parent_id is None:
        return []

    parent = tree.nodes.get(node.parent_id)

    if parent is None or parent.status != NodeStatus.WORKING:
        return []

    if not has_divergence(
        parent,
        node,
        tree.higher_is_better,
    ):
        return []

    return [{
        "action": "prune",
        "target": node.id,
        "note": (
            "C4: Validation improved while "
            "probe performance deteriorated."
        ),
    }]
