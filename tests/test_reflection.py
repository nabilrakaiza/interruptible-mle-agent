"""Stage 3: A4 reflection."""

import json
from pathlib import Path

import pytest
import yaml

from imle.agents import reflection as a4
from imle.agents.coding import LLMUnavailable
from imle.tree import Node, NodeStatus, Operator, Tree


def finding_reply(*items: tuple[str, str, list[str]]) -> str:
    return json.dumps({"findings": [{"text": t, "effect": e, "evidence": ev} for t, e, ev in items]})


class ScriptedLLM:
    """Canned replies in order; records prompts. An Exception instance in the list is raised instead."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts: list[str] = []
        self.agents: list[str] = []

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        self.prompts.append(user)
        self.agents.append(agent)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def make_tree(n: int) -> Tree:
    """n0..n(n-1): drafts with distinctive val, probe and test scores; n2 buggy."""
    t = Tree(higher_is_better=False)
    for i in range(n):
        buggy = i == 2
        t.add(Node(id=f"n{i}", operator=Operator.DRAFT, plan=f"Plan {i}: logistic regression on tf-idf.",
                   status=NodeStatus.BUGGY if buggy else NodeStatus.WORKING,
                   val_score=None if buggy else 0.4 + i / 100, probe_score=None if buggy else 0.777 + i / 1000,
                   test_score=None if buggy else 0.999, error="runtime_error: exit code 1" if buggy else None))
    return t


def run_dir_with(tmp_path: Path, num_drafts: int = 3, every_n: int = 2) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "config.yaml").write_text(yaml.safe_dump({"search": {"num_drafts": num_drafts},
                                                         "reflection": {"every_n": every_n}}))
    return run_dir


GOOD = finding_reply(("TF-IDF with logistic regression is a solid baseline.", "helps", ["n1", "n0"]))


def test_boundaries_after_drafts_then_every_n(tmp_path: Path):
    run_dir = run_dir_with(tmp_path, num_drafts=3, every_n=2)
    llm = ScriptedLLM(GOOD, finding_reply(("Char n-grams beat word n-grams on this data.", "helps", ["n4"])))
    findings: list = []
    called_at = []
    for n in range(1, 7):
        before = len(llm.prompts)
        findings = a4.reflect(llm, make_tree(n), findings, run_dir)
        if len(llm.prompts) > before:
            called_at.append(n)
    assert called_at == [3, 5]
    assert [f["evidence"][0]["node_id"] for f in findings] == ["n1", "n4"]
    assert llm.agents == ["reflection", "reflection"]


def test_finding_evidence_scores_come_from_the_tree(tmp_path: Path):
    run_dir = run_dir_with(tmp_path)
    tree = make_tree(3)
    f = a4.reflect(ScriptedLLM(GOOD), tree, [], run_dir)[0]
    assert f["step"] == 3 and f["effect"] == "helps" and f["id"].startswith("f-")
    assert f["evidence"] == [{"node_id": i, "val_score": tree.nodes[i].val_score,
                              "probe_score": tree.nodes[i].probe_score} for i in ("n1", "n0")]


def test_prompt_shows_validation_but_never_probe_or_test(tmp_path: Path):
    run_dir = run_dir_with(tmp_path)
    llm = ScriptedLLM(GOOD)
    a4.reflect(llm, make_tree(3), [], run_dir)
    prompt = llm.prompts[0]
    assert "validation 0.41" in prompt and "buggy (runtime_error)" in prompt
    assert "0.777" not in prompt and "0.778" not in prompt and "0.999" not in prompt
    assert "probe" not in prompt.lower()


def test_existing_findings_are_shown_and_duplicates_dropped(tmp_path: Path):
    run_dir = run_dir_with(tmp_path)
    first = a4.reflect(ScriptedLLM(GOOD), make_tree(3), [], run_dir)
    (run_dir / "a4" / "state.json").unlink()  # force another boundary at 3 nodes
    same_text = finding_reply(("tf-idf with Logistic Regression is a solid baseline", "helps", ["n0"]))
    llm = ScriptedLLM(same_text)
    again = a4.reflect(llm, make_tree(3), first, run_dir)
    assert again == first
    assert first[0]["id"] in llm.prompts[0]


def test_deleted_finding_is_not_written_again(tmp_path: Path):
    """After a `correct` deletes a finding, A4 is told so and the same finding is never added back."""
    from imle.apply import apply_pending
    from imle.intervention import Action, Intervention, append
    from imle.state import SearchState

    run_dir = run_dir_with(tmp_path, num_drafts=3, every_n=1)
    findings = a4.reflect(ScriptedLLM(GOOD), make_tree(3), [], run_dir)
    append(run_dir / "queue.jsonl", Intervention(id="c1", ts="2026-10-24T00:00:00Z", source="finding_correction",
                                                 action=Action.CORRECT, target=findings[0]["id"]))
    apply_pending(run_dir, make_tree(3), findings, SearchState())
    assert findings == []
    llm = ScriptedLLM(GOOD)   # the model states the deleted finding again
    again = a4.reflect(llm, make_tree(4), findings, run_dir)
    assert again == []
    assert "removed because later nodes contradicted them" in llm.prompts[0]
    assert "solid baseline" in llm.prompts[0]


def test_max_findings_keeps_newest():
    new = [a4.Finding.create(f"Finding number {i} about the data.", [a4.Evidence(node_id="n0")]) for i in range(4)]
    kept = a4.merge([], new, max_findings=3)
    assert [f["text"] for f in kept] == [f"Finding number {i} about the data." for i in (1, 2, 3)]


def test_malformed_json_is_retried(tmp_path: Path):
    run_dir = run_dir_with(tmp_path)
    llm = ScriptedLLM("Here are my findings: none", GOOD)
    findings = a4.reflect(llm, make_tree(3), [], run_dir)
    assert len(findings) == 1 and len(llm.prompts) == 2 and "not valid" in llm.prompts[1]


def test_unknown_node_ids_are_retried(tmp_path: Path):
    llm = ScriptedLLM(finding_reply(("A finding citing a node that does not exist.", "helps", ["n99"])), GOOD)
    findings = a4.reflect(llm, make_tree(3), [], run_dir_with(tmp_path))
    assert len(findings) == 1 and "n99" in llm.prompts[1]


def test_propose_fails_clearly_after_retries():
    llm = ScriptedLLM("x", "y", '{"findings": [{"text": "short", "effect": "helps", "evidence": ["n0"]}]}')
    with pytest.raises(a4.ReflectionError, match="3 attempts"):
        a4.propose(llm, make_tree(3), [], step=3, max_retries=2)


def test_reflect_logs_failure_and_keeps_findings(tmp_path: Path, capsys):
    run_dir = run_dir_with(tmp_path, every_n=2)
    existing = [{"id": "f-old", "text": "An older finding.", "evidence": []}]
    out = a4.reflect(ScriptedLLM("a", "b", "c"), make_tree(3), existing, run_dir)
    assert out == existing
    assert "A4 reflection failed" in capsys.readouterr().out
    errors = (run_dir / "a4" / "errors.jsonl").read_text().splitlines()
    assert json.loads(errors[0])["finished_nodes"] == 3
    assert json.loads((run_dir / "a4" / "state.json").read_text()) == {"next_boundary": 5, "written": {}}


def test_outage_propagates_and_boundary_stays_pending(tmp_path: Path):
    run_dir = run_dir_with(tmp_path)
    with pytest.raises(LLMUnavailable):
        a4.reflect(ScriptedLLM(LLMUnavailable("down")), make_tree(3), [], run_dir)
    assert len(a4.reflect(ScriptedLLM(GOOD), make_tree(4), [], run_dir)) == 1


def test_controller_runs_with_reflection(tmp_path: Path):
    """The real controller loop with A4: findings reach the checkpoint and A3's next prompts."""
    from test_controller import FakeEvaluator, FakeSandbox, make_cfg, reply

    from imle import checkpoint
    from imle.controller import Controller

    cfg = make_cfg(budget={"max_nodes": 4}, search={"num_drafts": 2})
    replies = [reply("Draft one."), reply("Draft two."),
               finding_reply(("Both drafts ran; a simple model is enough to start.", "neutral", ["n0", "n1"])),
               reply("Improve."), reply("Improve again.")]
    llm = ScriptedLLM(*replies)
    Controller(cfg, "toy-task", 0, tmp_path / "run", llm=llm, sandbox=FakeSandbox(), evaluator=FakeEvaluator(),
               reflect=a4.reflect).run()
    findings = checkpoint.read(tmp_path / "run")["findings"]
    assert [f["text"] for f in findings] == ["Both drafts ran; a simple model is enough to start."]
    assert llm.agents[2] == "reflection"
    assert "simple model is enough" in llm.prompts[3]  # A3's prompt after the boundary
