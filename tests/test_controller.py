import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from imle import checkpoint
from imle.controller import (
    Controller,
    beats,
    latest_complete_checkpoint,
    load_config,
    select_next,
)
from imle.execution import SubprocessSandbox
from imle.intervention import Action, Intervention, append
from imle.tree import Node, NodeStatus, Operator, Tree

REPO = Path(__file__).resolve().parents[1]

SCRIPT = """\
import os
import pandas as pd
train = pd.read_csv("input/train.csv")
predict = pd.read_csv("input/predict.csv")
print("train rows", len(train))
predict.assign(y=train["y"].mean()).to_csv(os.path.join(OUTPUT_DIR, "predictions.csv"), index=False)
"""


def reply(plan: str = "Predict the training mean.", script: str = SCRIPT) -> str:
    """A well-formed model reply with the given plan and script."""
    return f"PLAN: {plan}\n\n```python\n{script}```\n"


@dataclass
class Ctx:
    """Stand-in for the evaluator's TaskContext."""

    input_dir: Path
    description: str = "Predict y."
    prediction_format: str = "Columns id,y; one row per row of predict.csv."
    metric: str = "rmse"
    higher_is_better: bool = False


@dataclass
class Exec:
    """Stand-in for the sandbox's ExecResult. Defaults to a clean exit."""

    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    wall_time_s: float = 0.0
    timed_out: bool = False


@dataclass
class Score:
    """Stand-in for the evaluator's ScoreResult."""

    val_score: float | None = None
    probe_score: float | None = None
    error: str | None = None


class FakeEvaluator:
    """Scores nodes from a list instead of comparing predictions with labels."""

    def __init__(self, scores: list[float | None] | None = None):
        """`scores` are handed out one per scored node; None means invalid predictions."""
        self.scores = list(scores or [])
        self.screened: list[str] = []

    def prepare(self, task: str, run_dir: Path, seed: int) -> Ctx:
        """Write a two-row train.csv and predict.csv outside the workspace, as A1 might."""
        input_dir = run_dir / "prepared"
        input_dir.mkdir(parents=True)
        (input_dir / "train.csv").write_text("id,y\n1,0.0\n2,1.0\n")
        (input_dir / "predict.csv").write_text("id\n3\n4\n")
        return Ctx(input_dir=input_dir)

    def score(self, node_dir: Path) -> Score:
        """The next canned score if predictions exist; also writes submission.csv."""
        if not (node_dir / "output" / "predictions.csv").exists():
            return Score(error="predictions.csv not found")
        value = self.scores.pop(0) if self.scores else 0.5
        if value is None:
            return Score(error="wrong columns")
        (node_dir / "submission.csv").write_text(f"id,y\n4,{value}\n")
        return Score(val_score=value, probe_score=value + 0.1)


class FakeSandbox:
    """Pretends to run scripts: writes predictions.csv, or returns a scripted failure."""

    def __init__(self, outcomes: list[Exec] | None = None, on_run=None):
        """`outcomes` are used in order (clean exits after they run out); `on_run` gets each node's output folder."""
        self.outcomes = list(outcomes or [])
        self.on_run = on_run
        self.scripts: list[str] = []

    def output_path(self, output_dir: Path) -> str:
        """The host path, as the subprocess sandbox would use."""
        return str(output_dir)

    def run(self, script_path: Path, workspace: Path, output_dir: Path, timeout_s: float) -> Exec:
        """Record the executed script, then succeed or fail as scripted."""
        self.scripts.append(script_path.read_text())
        if self.on_run:
            self.on_run(output_dir)
        result = self.outcomes.pop(0) if self.outcomes else Exec()
        if result.exit_code == 0 and not result.timed_out:
            (output_dir / "predictions.csv").write_text("id,y\n3,0.5\n4,0.5\n")
        return result


class ScriptedLLM:
    """Returns canned replies in order (then a default reply) and records every prompt."""

    def __init__(self, replies: list[str] | None = None):
        """`replies` are returned one per call; after that, numbered default replies."""
        self.replies = list(replies or [])
        self.prompts: list[str] = []

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        """Record the prompt and return the next reply."""
        self.prompts.append(user)
        return self.replies.pop(0) if self.replies else reply(f"Attempt {len(self.prompts)}.")


def make_cfg(budget: dict | None = None, search: dict | None = None, **top) -> dict:
    """The C1 config with overrides; by default 2 drafts and 6 nodes."""
    cfg = load_config(REPO / "configs" / "conditions" / "c1_autonomous.yaml")
    cfg["budget"].update({"max_nodes": 6, **(budget or {})})
    cfg["search"].update({"num_drafts": 2, **(search or {})})
    cfg.update(top)
    return cfg


def make_controller(tmp_path: Path, cfg: dict | None = None, **deps) -> Controller:
    """A controller on fakes, writing to tmp_path/run."""
    deps.setdefault("llm", ScriptedLLM())
    deps.setdefault("sandbox", FakeSandbox())
    deps.setdefault("evaluator", FakeEvaluator())
    return Controller(cfg or make_cfg(), "toy-task", 0, tmp_path / "run", **deps)


def statuses(tree: Tree) -> list[str]:
    """Node statuses in creation order, as strings."""
    return [n.status.value for n in tree.nodes.values()]


SEARCH = {
    "num_drafts": 1, "debug_prob": 0.5, "max_debug_depth": 2, "improve_patience": 2, "improve_min_rel_gain": 0.01,
}


class FixedRandom(random.Random):
    """A Random whose random() always returns `value`, to force or block debugging."""

    def __init__(self, value: float):
        """`value` is what random() returns."""
        super().__init__(0)
        self.value = value

    def random(self) -> float:
        """Always the fixed value."""
        return self.value


def test_load_config_merges_and_expands(monkeypatch):
    """A condition file overrides base.yaml key by key, and ${LLM_MODEL} is filled in."""
    monkeypatch.setenv("LLM_MODEL", "some-model")
    cfg = load_config(REPO / "configs" / "conditions" / "ablation_a4_off.yaml")
    assert cfg["condition"] == "A4-off"
    assert cfg["agents"] == {"evaluation": True, "retrieval": True, "reflection": False}
    assert cfg["llm"]["model"] == "some-model"
    assert cfg["sandbox"]["backend"] == "docker"


def test_select_drafts_first_then_improves_best():
    """Drafts come first; then the best working node is improved."""
    tree = Tree(higher_is_better=True)
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.DRAFT, None)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5))
    tree.add(Node(id="n1", parent_id="n0", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.7))
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.IMPROVE, "n1")


def test_select_skips_exhausted_nodes():
    """After improve_patience failed improvements a node is skipped; with none left, draft."""
    tree = Tree(higher_is_better=True)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5))
    tree.add(Node(id="n1", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.8))
    tree.add(Node(id="n2", parent_id="n1", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.7))
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.IMPROVE, "n1")  # one failed attempt so far
    tree.add(Node(id="n3", parent_id="n1", operator=Operator.IMPROVE, status=NodeStatus.BUGGY))
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.IMPROVE, "n2")  # n1 is exhausted
    tree.nodes["n2"].status = NodeStatus.PRUNED
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.IMPROVE, "n0")
    tree.nodes["n0"].status = NodeStatus.PRUNED
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.DRAFT, None)  # only exhausted n1 is left


def test_beats_uses_a_relative_threshold():
    """A gain counts only above improve_min_rel_gain relative to the old score, in the metric's direction."""
    up, down = Tree(higher_is_better=True), Tree(higher_is_better=False)
    assert not beats(up, 0.801, 0.8, 0.01) and beats(up, 0.81, 0.8, 0.01)
    assert beats(down, 0.39, 0.4, 0.01) and not beats(down, 0.41, 0.4, 0.01)


def test_select_debugs_up_to_max_depth():
    """A buggy leaf with a script is debugged when the coin says so, until max_debug_depth."""
    tree = Tree()
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.BUGGY, script_path="s"))
    assert select_next(tree, SEARCH, FixedRandom(0.0)) == (Operator.DEBUG, "n0")
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.DEBUG, "n0")  # nothing to improve
    tree.add(Node(id="n1", parent_id="n0", operator=Operator.DEBUG, status=NodeStatus.BUGGY, script_path="s"))
    tree.add(Node(id="n2", parent_id="n1", operator=Operator.DEBUG, status=NodeStatus.BUGGY, script_path="s"))
    assert select_next(tree, SEARCH, FixedRandom(0.0)) == (Operator.DRAFT, None)
    tree.add(Node(id="n3", operator=Operator.DRAFT, status=NodeStatus.BUGGY))  # no script: generation error
    assert select_next(tree, SEARCH, FixedRandom(0.0)) == (Operator.DRAFT, None)


def test_end_to_end_with_real_subprocess(tmp_path: Path):
    """Real scripts run in the shared workspace, read ./input and write to OUTPUT_DIR."""
    cfg = make_cfg(budget={"max_nodes": 4}, search={"debug_prob": 0.0})
    c = make_controller(tmp_path, cfg, sandbox=SubprocessSandbox(), evaluator=FakeEvaluator([0.9, 0.4, 0.3, 0.35]))
    tree = c.run()

    assert [n.operator.value for n in tree.nodes.values()] == ["draft", "draft", "improve", "improve"]
    assert [n.parent_id for n in tree.nodes.values()] == [None, None, "n1", "n2"]
    assert statuses(tree) == ["working"] * 4
    assert (c.run_dir / "nodes" / "n0" / "output" / "predictions.csv").read_text() == "id,y\n3,0.5\n4,0.5\n"
    assert (c.run_dir / "workspace" / "input" / "train.csv").exists()
    assert (c.run_dir / "workspace" / "n0.py").read_text().startswith("OUTPUT_DIR = ")
    assert tree.nodes["n0"].script_path == "nodes/n0/solution.py"
    assert (c.run_dir / "submission.csv").read_text() == "id,y\n4,0.3\n"

    final = checkpoint.read(c.run_dir)["status"]
    assert final["done"] and final["final_node"] == "n2" and final["final_selection"] == "best_val"
    assert final["stop_reason"] == "max_nodes"


def test_failures_become_buggy_nodes(tmp_path: Path):
    """Each failure stage gives a buggy node with its own error category, and the run carries on."""
    llm = ScriptedLLM(["no code here", "still no code"])
    sandbox = FakeSandbox([Exec(timed_out=True), Exec(exit_code=1, stderr="Traceback ...\nKeyError: 'text'")])
    cfg = make_cfg(budget={"max_nodes": 5}, search={"num_drafts": 5})
    c = make_controller(tmp_path, cfg, llm=llm, sandbox=sandbox, evaluator=FakeEvaluator([None, 0.3]))
    nodes = list(c.run().nodes.values())

    assert statuses(c.tree) == ["buggy"] * 4 + ["working"]
    assert [n.error.split(":")[0] for n in nodes[:4]] == [
        "generation_error", "timeout", "runtime_error", "invalid_submission",
    ]
    assert "KeyError: 'text'" in nodes[2].error
    assert checkpoint.read(c.run_dir)["status"]["final_node"] == "n4"


def test_debug_and_improve_prompts_carry_the_parent(tmp_path: Path):
    """A debug sees the failed script and its error; an improve sees the score and printed output."""
    sandbox = FakeSandbox([Exec(exit_code=1, stderr="KeyError: 'text'"), Exec(stdout="fold auc 0.71")])
    cfg = make_cfg(budget={"max_nodes": 3}, search={"num_drafts": 1, "debug_prob": 1.0})
    llm = ScriptedLLM([reply("First draft.", "print('draft one')\n")])
    c = make_controller(tmp_path, cfg, llm=llm, sandbox=sandbox, evaluator=FakeEvaluator([0.25]))
    tree = c.run()

    assert [(n.operator.value, n.parent_id) for n in tree.nodes.values()] == [
        ("draft", None), ("debug", "n0"), ("improve", "n1"),
    ]
    debug_prompt, improve_prompt = llm.prompts[1], llm.prompts[2]
    assert "print('draft one')" in debug_prompt and "KeyError: 'text'" in debug_prompt
    assert "It scores 0.25 on the validation split" in improve_prompt and "fold auc 0.71" in improve_prompt


def test_stops_on_budget_without_submission(tmp_path: Path):
    """The search stops when the wall clock runs out, and writes no submission if nothing worked."""

    class SlowFail(FakeSandbox):
        """A sandbox whose script outlasts the whole budget and then fails."""

        def run(self, script_path, workspace, output_dir, timeout_s):
            """Sleep past the budget, then report a crash."""
            time.sleep(0.2)
            return Exec(exit_code=1)

    c = make_controller(tmp_path, make_cfg(budget={"wall_clock_s": 0.1}), sandbox=SlowFail())
    assert len(c.run().nodes) == 1
    status = checkpoint.read(c.run_dir)["status"]
    assert status["stop_reason"] == "budget" and status["final_node"] is None
    assert not (c.run_dir / "submission.csv").exists()


def test_interventions_apply_at_safe_points(tmp_path: Path):
    """Queued redirect, override and rebudget change the search and the final submission."""
    queue = tmp_path / "run" / "queue.jsonl"

    def queue_during(output_dir: Path) -> None:
        """While n1 runs, a monitor redirects the next node and overrides the final choice."""
        if output_dir.parent.name == "n1":
            append(queue, Intervention(id="q1", ts="2026-10-18T00:00:01Z", source="human",
                                       action=Action.REDIRECT, target="n0", params={"operator": "improve"}))
            append(queue, Intervention(id="q2", ts="2026-10-18T00:00:02Z", source="human",
                                       action=Action.OVERRIDE, target="n0"))
            append(queue, Intervention(id="q3", ts="2026-10-18T00:00:03Z", source="human",
                                       action=Action.REBUDGET, params={"seconds": 60}))

    cfg = make_cfg(budget={"max_nodes": 3}, search={"debug_prob": 0.0})
    c = make_controller(tmp_path, cfg, sandbox=FakeSandbox(on_run=queue_during),
                        evaluator=FakeEvaluator([0.9, 0.2, 0.1]))
    tree = c.run()

    assert tree.nodes["n2"].operator == Operator.IMPROVE and tree.nodes["n2"].parent_id == "n0"
    applied = [json.loads(line) for line in (c.run_dir / "applied.jsonl").read_text().splitlines()]
    assert [(a["intervention"]["id"], a["outcome"]) for a in applied] == [
        ("q1", "applied"), ("q2", "applied"), ("q3", "applied"),
    ]
    final = checkpoint.read(c.run_dir)["status"]
    assert final["final_node"] == "n0" and final["final_selection"] == "override"
    assert final["search"]["extra_budget_s"] == 60


def test_top_k_and_override_fallback(tmp_path: Path):
    """top_k writes one submission per chosen node; an override on a missing node falls back to the ranking."""
    cfg = make_cfg(budget={"max_nodes": 4}, search={"num_drafts": 4}, final_selection="top_k", top_k=2)
    c = make_controller(tmp_path, cfg, evaluator=FakeEvaluator([0.5, 0.2, 0.3, 0.9]))
    c.state.override_node = "n9"
    c.run()
    final = checkpoint.read(c.run_dir)["status"]
    assert final["final_nodes"] == ["n1", "n2"]
    assert final["final_selection"] == "top_k; override target no longer working"
    assert (c.run_dir / "final" / "submission_2.csv").read_text() == "id,y\n4,0.3\n"
    assert (c.run_dir / "submission.csv").read_text() == "id,y\n4,0.2\n"


def test_resume_after_crash(tmp_path: Path):
    """A crash mid-node loses only that node; resume continues the tree, budget and step count."""

    class Crashing(FakeEvaluator):
        """Raises on the third score, like a machine going down mid-run."""

        def score(self, node_dir):
            """Crash on n2, otherwise score normally."""
            if node_dir.name == "n2":
                raise RuntimeError("power cut")
            return super().score(node_dir)

    cfg = make_cfg(budget={"max_nodes": 4}, search={"num_drafts": 4})
    with pytest.raises(RuntimeError):
        make_controller(tmp_path, cfg, evaluator=Crashing([0.5, 0.4])).run()
    run_dir = tmp_path / "run"
    (run_dir / "checkpoints" / "000099").mkdir()  # a checkpoint cut short: no status.json
    assert latest_complete_checkpoint(run_dir)["step"] == 2

    c = Controller.resume(run_dir, llm=ScriptedLLM(), sandbox=FakeSandbox(), evaluator=FakeEvaluator([0.3, 0.2]))
    assert list(c.tree.nodes) == ["n0", "n1"] and c.state.step == 3
    assert next(iter((run_dir / "nodes" / "_unfinished").iterdir())).name.startswith("n2_")
    assert checkpoint.latest_step(run_dir) == 2  # the cut-short checkpoint no longer shadows new ones
    tree = c.run()
    assert list(tree.nodes) == ["n0", "n1", "n2", "n3"]
    assert checkpoint.read(run_dir)["status"]["final_node"] == "n3"

    again = Controller.resume(run_dir, llm=ScriptedLLM(), sandbox=FakeSandbox(), evaluator=FakeEvaluator())
    assert again.done and len(again.run().nodes) == 4


def test_reflection_screen_and_cards(tmp_path: Path):
    """Findings from A4 and the task's model cards reach the prompt; A1's screen can block a script."""
    llm = ScriptedLLM()

    def reflect(llm_, tree, findings, run_dir):
        """A4 stand-in: one finding about the latest node."""
        last = list(tree.nodes)[-1]
        return [{"id": "f1", "text": "means work", "evidence": [{"node_id": last, "val_score": 0.5}]}]

    class Screening(FakeEvaluator):
        """A1 stand-in whose leakage screen rejects the second script."""

        def screen(self, llm_, script):
            """Flag the second script it sees."""
            self.screened.append(script)
            return "reads labels of predict rows" if len(self.screened) == 2 else None

    sandbox = FakeSandbox()
    c = Controller(make_cfg(budget={"max_nodes": 2}), "spooky-author-identification", 0, tmp_path / "run",
                   llm=llm, sandbox=sandbox, evaluator=Screening(), reflect=reflect)
    tree = c.run()

    assert "<model_cards>" in llm.prompts[0] and "TF-IDF" in llm.prompts[0]
    assert "[f1] means work (evidence: n0=0.5)" in llm.prompts[1]
    assert tree.nodes["n1"].error == "leakage: reads labels of predict rows"
    assert len(sandbox.scripts) == 1
    assert checkpoint.read(c.run_dir)["findings"][0]["id"] == "f1"


def test_ablation_switches(tmp_path: Path):
    """With reflection and retrieval off, no findings or hand-written cards reach the prompt."""
    llm = ScriptedLLM()
    cfg = make_cfg(budget={"max_nodes": 2}, agents={"evaluation": True, "retrieval": False, "reflection": False})
    calls = []
    c = Controller(cfg, "spooky-author-identification", 0, tmp_path / "run", llm=llm, sandbox=FakeSandbox(),
                   evaluator=FakeEvaluator(), reflect=lambda *a: calls.append(a) or [])
    c.run()
    assert calls == []
    assert all("<model_cards>" not in p for p in llm.prompts)


def test_improve_prompt_lists_attempts_that_did_not_help(tmp_path: Path):
    """Earlier improve attempts on the same node, worse or failed, are shown so the model tries something new."""
    sandbox = FakeSandbox([Exec(), Exec(), Exec(exit_code=1, stderr="boom")])
    cfg = make_cfg(budget={"max_nodes": 4}, search={"num_drafts": 1, "debug_prob": 0.0})
    llm = ScriptedLLM()
    c = make_controller(tmp_path, cfg, llm=llm, sandbox=sandbox, evaluator=FakeEvaluator([0.5, 0.6]))
    tree = c.run()

    assert [n.parent_id for n in tree.nodes.values()] == [None, "n0", "n0", "n0"]
    assert "already tried" not in llm.prompts[1]
    last = llm.prompts[3]
    assert "- Attempt 2. -> validation 0.6000, not better" in last
    assert "- Attempt 3. -> failed (runtime_error)" in last
