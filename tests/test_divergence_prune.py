import importlib.util
from pathlib import Path

import pytest

from imle import checkpoint
from imle.apply import apply_pending
from imle.controller import load_config, load_policies
from imle.intervention import Intervention, append
from imle.policies import divergence_prune as c4
from imle.state import SearchState
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("replay_policy", ROOT / "scripts" / "replay_policy.py")
replay_policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay_policy)

W, B = NodeStatus.WORKING, NodeStatus.BUGGY
D, IMP, DBG = Operator.DRAFT, Operator.IMPROVE, Operator.DEBUG
# Lower is better. n0 -> n1 -> n2 improves validation while probe gets worse; n3 is another draft.
DIVERGING = [
    ("n0", D, None, W, 0.50, 0.50, 0.50),
    ("n1", IMP, "n0", W, 0.45, 0.55, 0.55),
    ("n2", IMP, "n1", W, 0.40, 0.56, 0.56),
    ("n3", D, None, W, 0.60, 0.60, 0.60),
]


def make_tree(nodes: list[tuple] = DIVERGING) -> Tree:
    """A tree from (id, operator, parent, status, val, probe, test) tuples, lower is better."""
    tree = Tree(higher_is_better=False)
    for nid, op, parent, status, val, probe, test in nodes:
        tree.add(Node(id=nid, operator=op, parent_id=parent, status=status, val_score=val, probe_score=probe,
                      test_score=test))
    return tree


def ck(tree: Tree, current: str, step: int = 1) -> dict:
    """A checkpoint dict as the controller passes it to decide()."""
    return {"step": step, "tree": tree.model_dump(mode="json"), "findings": [], "status": {"current_node": current}}


def test_prunes_below_the_best_probe_node(tmp_path: Path):
    """Validation up and probe down over two nodes since n0: prune n1's subtree, keep n0."""
    [item] = c4.decide(tmp_path, ck(make_tree(), "n2"))
    assert item["action"] == "prune" and item["target"] == "n1"
    assert item["params"]["anchor"] == "n0" and item["params"]["steps"] == 2
    assert item["params"]["val_gain"] == pytest.approx(0.2) and item["params"]["probe_loss"] == pytest.approx(0.12)
    assert "since n0" in item["note"]


def test_one_node_is_not_a_trend(tmp_path: Path):
    """After n1 alone (one step since the anchor) nothing is pruned."""
    assert c4.decide(tmp_path, ck(make_tree(), "n1")) == []


@pytest.mark.parametrize("val, probe", [(0.498, 0.56), (0.40, 0.503)])
def test_small_changes_are_ignored(tmp_path: Path, val: float, probe: float):
    """A validation gain or probe loss under 1% does not count."""
    nodes = DIVERGING[:2] + [("n2", IMP, "n1", W, val, probe, None)] + DIVERGING[3:]
    assert c4.decide(tmp_path, ck(make_tree(nodes), "n2")) == []


def test_buggy_nodes_in_the_lineage_are_skipped(tmp_path: Path):
    """A buggy node between two working ones is not counted as a step and is not an anchor."""
    nodes = [DIVERGING[0], ("nb", IMP, "n0", B, None, None, None), ("n1", DBG, "nb", W, 0.45, 0.55, None),
             ("n2", IMP, "n1", W, 0.40, 0.56, None), DIVERGING[3]]
    [item] = c4.decide(tmp_path, ck(make_tree(nodes), "n2"))
    assert item["target"] == "nb" and item["params"]["steps"] == 2


def test_the_anchor_stays_selectable(tmp_path: Path):
    """Even with no other draft, the anchor n0 is outside the pruned subtree, so something is left to submit."""
    [item] = c4.decide(tmp_path, ck(make_tree(DIVERGING[:3]), "n2"))
    assert item["target"] == "n1" and "n0" not in make_tree(DIVERGING[:3]).subtree_ids(item["target"])


def test_unscored_or_unknown_nodes_are_ignored(tmp_path: Path):
    """A buggy current node, or none at all (step 0), asks for nothing."""
    nodes = DIVERGING + [("n4", IMP, "n2", B, None, None, None)]
    assert c4.decide(tmp_path, ck(make_tree(nodes), "n4")) == []
    assert c4.decide(tmp_path, ck(make_tree(), None)) == []


# The next five cases come from Sahi's C4 tests (sahi-interaction), adapted to the shared rule.
def test_higher_is_better_metrics(tmp_path: Path):
    """The same divergence on an AUC-like metric, where higher is better, is pruned."""
    tree = Tree(higher_is_better=True)
    for nid, parent, val, probe in [("n0", None, 0.80, 0.79), ("n1", "n0", 0.86, 0.76), ("n2", "n1", 0.92, 0.75)]:
        tree.add(Node(id=nid, operator=IMP if parent else D, parent_id=parent, status=W, val_score=val,
                      probe_score=probe))
    [item] = c4.decide(tmp_path, ck(tree, "n2"))
    assert item["target"] == "n1" and item["params"]["anchor"] == "n0"


def test_missing_probe_score_asks_for_nothing(tmp_path: Path):
    """A node scored on validation only (e.g. a probe scoring failure) is not judged."""
    nodes = DIVERGING[:2] + [("n2", IMP, "n1", W, 0.40, None, None)]
    assert c4.decide(tmp_path, ck(make_tree(nodes), "n2")) == []


def test_test_scores_are_never_used(tmp_path: Path):
    """Changing the hidden test scores does not change the decision."""
    nodes = [(nid, op, parent, status, val, probe, 0.0) for nid, op, parent, status, val, probe, _ in DIVERGING]
    assert c4.decide(tmp_path, ck(make_tree(nodes), "n2")) == c4.decide(tmp_path, ck(make_tree(), "n2"))


def test_prune_goes_through_apply_pending_once(tmp_path: Path):
    """The queued prune is applied by A5, removes n1's subtree, and the next safe point asks for nothing."""
    tree = make_tree()
    for i, action in enumerate(c4.decide(tmp_path, ck(tree, "n2"))):
        append(tmp_path / "queue.jsonl", Intervention.model_validate(
            {**action, "id": f"divergence_prune-s1-{i}", "ts": "2026-10-24T00:00:00Z", "source": "divergence_prune"}))
    [record] = apply_pending(tmp_path, tree, [], SearchState())
    assert record.outcome == "applied"
    assert {n.id for n in tree.selectable()} == {"n0", "n3"}
    assert apply_pending(tmp_path, tree, [], SearchState()) == []
    assert c4.decide(tmp_path, ck(tree, "n2")) == []


def test_bootstrap_share_must_be_consistent(tmp_path: Path, monkeypatch):
    """With stand-in labels, a probe loss that holds in under 95% of resamples is treated as noise."""
    monkeypatch.setattr(c4.stand_in_evaluation, "paired_worse_share", lambda *a, **k: 0.9)
    assert c4.decide(tmp_path, ck(make_tree(), "n2")) == []
    monkeypatch.setattr(c4.stand_in_evaluation, "paired_worse_share", lambda *a, **k: 0.99)
    assert c4.decide(tmp_path, ck(make_tree(), "n2"))[0]["params"]["consistent_share"] == 0.99


def test_thresholds_come_from_the_run_config(tmp_path: Path):
    """policies.divergence_prune in config.yaml overrides the defaults."""
    (tmp_path / "config.yaml").write_text("policies: {divergence_prune: {min_steps: 3}}\n")
    assert c4.settings(tmp_path)["min_steps"] == 3 and c4.settings(tmp_path)["min_val_gain"] == 0.01
    assert c4.decide(tmp_path, ck(make_tree(), "n2")) == []


def test_c4_condition_loads_the_policy():
    """The C4 condition's monitor resolves to this decide(), with the thresholds from base.yaml."""
    cfg = load_config(ROOT / "configs" / "conditions" / "c4_divergence_prune.yaml")
    assert load_policies(cfg) == {"divergence_prune": c4.decide}
    assert cfg["policies"]["divergence_prune"] == c4.DEFAULTS


def write_run(run_dir: Path, nodes: list[tuple]) -> None:
    """A finished C1 run with one checkpoint per node, each holding the tree as it was then."""
    tree = Tree(higher_is_better=False)
    checkpoint.write(run_dir, 0, tree.model_dump(mode="json"), [], {"current_node": None})
    for step, (nid, op, parent, status, val, probe, test) in enumerate(nodes, start=1):
        tree.add(Node(id=nid, operator=op, parent_id=parent, status=status, val_score=val, probe_score=probe,
                      test_score=test))
        checkpoint.write(run_dir, step, tree.model_dump(mode="json"), [], {"current_node": nid})


def test_replay_applies_prunes_and_compares_final_picks(tmp_path: Path):
    """The replay prunes after n2, skips n4 (below the pruned node), and the final pick moves to n0."""
    run = tmp_path / "runs" / "C1_toy_seed0"
    write_run(run, DIVERGING + [("n4", IMP, "n2", W, 0.30, 0.70, 0.70)])
    events, roots = replay_policy.replay(run, c4, {})
    assert [(e["after_node"], e["target"], e["nodes_removed"]) for e in events] == [("n2", "n1", 2)]
    row = replay_policy.summarise(run, events, roots)
    assert (row["nodes_pruned"], row["c1_pick"], row["c1_test"]) == (3, "n4", 0.70)
    assert (row["policy_pick"], row["policy_test"]) == ("n0", 0.50)


def test_replay_overrides_thresholds(tmp_path: Path):
    """--set values reach the policy for the replay only."""
    run = tmp_path / "run"
    write_run(run, DIVERGING)
    assert replay_policy.replay(run, c4, {"min_steps": 3})[0] == []
    assert c4.settings(run)["min_steps"] == 2  # restored afterwards
    assert replay_policy.find_runs([tmp_path]) == [run]
    assert replay_policy.parse_overrides(["min_steps=3", "min_val_gain=0.02"]) == {"min_steps": 3,
                                                                                  "min_val_gain": 0.02}
