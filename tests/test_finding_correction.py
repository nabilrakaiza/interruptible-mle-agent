"""Stage 5: the C5 finding-correction policy."""

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from imle import checkpoint
from imle.intervention import Action, Intervention, append
from imle.policies import finding_correction as c5
from imle.tree import Node, NodeStatus, Operator, Tree


def make_tree(higher_is_better: bool = True) -> Tree:
    """n0 draft; n1 improve that replicates on probe; n2 improve whose val gain is not matched; n3 buggy."""
    t = Tree(higher_is_better=higher_is_better)
    s = 1 if higher_is_better else -1
    t.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5, probe_score=0.5))
    t.add(Node(id="n1", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.WORKING,
               val_score=0.5 + s * 0.05, probe_score=0.5 + s * 0.04))
    t.add(Node(id="n2", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.WORKING,
               val_score=0.5 + s * 0.05, probe_score=0.5 - s * 0.01))
    t.add(Node(id="n3", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.BUGGY))
    return t


def finding(fid: str, effect: str, *node_ids: str) -> dict:
    return {"id": fid, "text": f"finding {fid}", "effect": effect, "evidence": [{"node_id": i} for i in node_ids]}


def ck(tree: Tree, *findings: dict) -> dict:
    return {"step": 3, "tree": tree.model_dump(mode="json"), "findings": list(findings), "status": {}}


def targets(decided: list[dict]) -> list[str]:
    return [d["target"] for d in decided]


@pytest.mark.parametrize("higher_is_better", [True, False])
def test_val_gain_not_matched_on_probe_is_deleted(tmp_path: Path, higher_is_better: bool):
    t = make_tree(higher_is_better)
    decided = c5.decide(tmp_path, ck(t, finding("f-good", "helps", "n1"), finding("f-bad", "helps", "n2")))
    assert targets(decided) == ["f-bad"]
    assert decided[0]["action"] == "correct" and "n2 val +0.05, probe -0.01 vs n0" in decided[0]["note"]
    assert "params" not in decided[0]   # no replacement: delete


def test_status_failures(tmp_path: Path):
    t = make_tree()
    t.nodes["n1"].status = NodeStatus.PRUNED
    decided = c5.decide(tmp_path, ck(t, finding("f-pruned", "helps", "n1"), finding("f-gone", "neutral", "n9"),
                                     finding("f-buggy", "helps", "n3")))
    assert targets(decided) == ["f-pruned", "f-gone", "f-buggy"]


def test_hurts_findings_may_cite_crashes_and_check_drops(tmp_path: Path):
    t = make_tree()
    t.nodes["n1"].val_score, t.nodes["n1"].probe_score = 0.45, 0.46   # val drop of 0.05, probe drop of 0.04
    t.nodes["n2"].val_score, t.nodes["n2"].probe_score = 0.45, 0.52   # val drop, probe went up
    decided = c5.decide(tmp_path, ck(t, finding("f-crash", "hurts", "n3"), finding("f-ok", "hurts", "n1"),
                                     finding("f-no", "hurts", "n2")))
    assert targets(decided) == ["f-no"]


def test_unchecked_nodes_and_fail_fraction(tmp_path: Path):
    t = make_tree()
    assert c5.decide(tmp_path, ck(t, finding("f-draft", "helps", "n0"))) == []           # no parent to compare
    assert c5.decide(tmp_path, ck(t, finding("f-neutral", "neutral", "n2"))) == []       # status checks only
    half = finding("f-half", "helps", "n1", "n2")
    assert targets(c5.decide(tmp_path, ck(t, half))) == ["f-half"]                       # 1 of 2 >= 0.5
    assert c5.decide(tmp_path, ck(t, half), min_fail_fraction=0.75) == []


def test_thresholds_from_arguments_then_config(tmp_path: Path):
    bad = ck(make_tree(), finding("f-bad", "helps", "n2"))     # gap 0.06
    assert c5.decide(tmp_path, bad, max_gap=0.1) == []
    (tmp_path / "config.yaml").write_text(yaml.safe_dump({"finding_correction": {"max_gap": 0.1}}))
    assert c5.decide(tmp_path, bad) == []
    assert targets(c5.decide(tmp_path, bad, max_gap=0.05)) == ["f-bad"]
    assert c5.thresholds(tmp_path) == {"max_gap": 0.1, "min_fail_fraction": 0.5}


def test_condition_file_states_the_thresholds():
    cfg = yaml.safe_load((Path(__file__).resolve().parents[1] / "configs/conditions/c5_finding_correction.yaml")
                         .read_text())
    assert cfg["monitors"] == ["finding_correction"]
    assert cfg["finding_correction"] == {"max_gap": c5.MAX_GAP, "min_fail_fraction": c5.MIN_FAIL_FRACTION}


def test_never_submits_twice(tmp_path: Path):
    bad = ck(make_tree(), finding("f-bad", "helps", "n2"))
    append(tmp_path / "queue.jsonl", Intervention(id="x", ts="2026-10-24T00:00:00Z", source="finding_correction",
                                                  action=Action.CORRECT, target="f-bad"))
    assert c5.decide(tmp_path, bad) == []
    (tmp_path / "queue.jsonl").unlink()
    (tmp_path / "applied.jsonl").write_text(json.dumps({"intervention": {"id": "y", "action": "correct",
                                                                         "target": "f-bad"}}) + "\n")
    assert c5.decide(tmp_path, bad) == []


def test_empty_checkpoint(tmp_path: Path):
    assert c5.decide(tmp_path, None) == [] and c5.decide(tmp_path, ck(make_tree())) == []


# --------------------------------------------------------------------------- through the controller


@dataclass
class Score:
    val_score: float | None = None
    probe_score: float | None = None
    error: str | None = None


def test_controller_deletes_a_finding_that_does_not_replicate(tmp_path: Path):
    """A4 writes a finding citing n1; n1's validation gain is not matched on the probe, so C5 deletes it."""
    from test_controller import REPO, FakeEvaluator, FakeSandbox, ScriptedLLM, reply

    from imle.agents import reflection as a4
    from imle.controller import Controller, load_config, load_policies

    class Evaluator(FakeEvaluator):
        """rmse-like (lower is better): n1 improves validation by 0.1 while the probe gets worse."""

        def score(self, node_dir: Path) -> Score:
            return {"n0": Score(0.5, 0.5), "n1": Score(0.4, 0.55)}.get(node_dir.name, Score(0.45, 0.45))

    cfg = load_config(REPO / "configs" / "conditions" / "c5_finding_correction.yaml")
    cfg["budget"].update({"max_nodes": 2})
    cfg["search"].update({"num_drafts": 1})
    cfg["reflection"] = {"every_n": 1}
    claim = json.dumps({"findings": [{"text": "Adding word bigrams lowered the validation error.",
                                      "effect": "helps", "evidence": ["n1"]}]})
    llm = ScriptedLLM([reply("Draft."), '{"findings": []}', reply("Add bigrams."), claim])
    run_dir = tmp_path / "run"
    Controller(cfg, "toy-task", 0, run_dir, llm=llm, sandbox=FakeSandbox(), evaluator=Evaluator(),
               reflect=a4.reflect, policies=load_policies(cfg)).run()

    applied = [json.loads(line) for line in (run_dir / "applied.jsonl").read_text().splitlines()]
    assert [(r["intervention"]["source"], r["intervention"]["action"], r["outcome"]) for r in applied] == [
        ("finding_correction", "correct", "applied")]
    assert "n1 val +0.1, probe -0.05 vs n0" in applied[0]["intervention"]["note"]
    steps = sorted(int(p.name) for p in (run_dir / "checkpoints").iterdir() if p.name.isdigit())
    with_finding = [s for s in steps if checkpoint.read(run_dir, s)["findings"]]
    assert with_finding and checkpoint.read(run_dir)["findings"] == []
