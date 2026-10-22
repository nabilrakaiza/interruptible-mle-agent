import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from imle import checkpoint
from imle.agents.coding import LLMUnavailable
from imle.controller import (
    Controller,
    beats,
    improve_failures,
    latest_complete_checkpoint,
    load_config,
    machine_info,
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

    def __init__(self, outcomes: list[Exec] | None = None, on_run=None, same_predictions: bool = False):
        """`outcomes` are used in order (clean exits after they run out); `on_run` gets each node's output folder.

        Each run writes different predictions, unless `same_predictions` is set.
        """
        self.outcomes = list(outcomes or [])
        self.on_run = on_run
        self.same_predictions = same_predictions
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
            y = 0.5 if self.same_predictions else len(self.scripts) / 100
            (output_dir / "predictions.csv").write_text(f"id,y\n3,0.5\n4,{y}\n")
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


def test_explore_prob_sometimes_improves_another_node():
    """With explore_prob, a low draw improves a random non-best open node; a high draw stays greedy."""
    tree = Tree(higher_is_better=True)
    for i, score in enumerate((0.5, 0.6, 0.7)):
        tree.add(Node(id=f"n{i}", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=score))
    search = {**SEARCH, "num_drafts": 3, "explore_prob": 0.15}
    assert select_next(tree, search, FixedRandom(0.9)) == (Operator.IMPROVE, "n2")
    assert select_next(tree, search, FixedRandom(0.1)) in {(Operator.IMPROVE, "n0"), (Operator.IMPROVE, "n1")}
    rng = random.Random(0)  # every improve explores: each non-best node gets picked, the best never
    picks = {select_next(tree, {**search, "explore_prob": 1.0}, rng)[1] for _ in range(50)}
    assert picks == {"n0", "n1"}


def test_explore_prob_zero_draws_no_random_number():
    """Without exploration the random state is untouched, so runs from before explore_prob replay the same."""
    tree = Tree(higher_is_better=True)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5))
    tree.add(Node(id="n1", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.6))
    rng = random.Random(0)
    before = rng.getstate()
    assert select_next(tree, {**SEARCH, "num_drafts": 2}, rng) == (Operator.IMPROVE, "n1")
    assert rng.getstate() == before


def test_select_skips_exhausted_nodes():
    """After improve_patience failed improvements a chain is skipped, its failed children too; with none left, draft."""
    tree = Tree(higher_is_better=True)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5))
    tree.add(Node(id="n1", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.8))
    tree.add(Node(id="n2", parent_id="n1", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.7))
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.IMPROVE, "n1")  # one failed attempt so far
    tree.add(Node(id="n3", parent_id="n1", operator=Operator.IMPROVE, status=NodeStatus.BUGGY))
    # n1 is exhausted, and so is n2: it is one of n1's failed attempts, not a fresh start
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.IMPROVE, "n0")
    tree.nodes["n0"].status = NodeStatus.PRUNED
    assert select_next(tree, SEARCH, FixedRandom(0.9)) == (Operator.DRAFT, None)  # only exhausted nodes are left


def test_a_chain_of_tiny_gains_runs_out_of_patience():
    """Gains below improve_min_rel_gain share one patience count along the chain; a real gain starts afresh."""
    search = {**SEARCH, "improve_patience": 3, "improve_min_rel_gain": 0.01}
    tree = Tree(higher_is_better=False)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.6))
    tree.add(Node(id="n1", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5))
    for i, val in enumerate([0.4999, 0.4998, 0.4997], start=2):  # each beats its parent by about 0.02%
        tree.add(Node(id=f"n{i}", parent_id=f"n{i - 1}" if i > 2 else "n1", operator=Operator.IMPROVE,
                      status=NodeStatus.WORKING, val_score=val))
    assert improve_failures(tree, search) == {"n0": 0, "n1": 3, "n2": 3, "n3": 3, "n4": 3}  # one shared chain
    assert select_next(tree, search, FixedRandom(0.9)) == (Operator.IMPROVE, "n0")  # the chain from n1 is spent

    tree.add(Node(id="n5", parent_id="n4", operator=Operator.IMPROVE, status=NodeStatus.WORKING, val_score=0.45))
    assert improve_failures(tree, search)["n5"] == 0  # a 10% gain is a fresh start
    assert select_next(tree, search, FixedRandom(0.9)) == (Operator.IMPROVE, "n5")


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


def test_retrieval_runs_once_and_survives_resume(tmp_path: Path):
    """A2 is called on the first draft only; its cards reach every draft, and a resume reuses the saved cards."""
    calls = []

    def retrieve(llm, task, ctx, run_dir):
        """Record the call and save one card, as WebRetriever would."""
        calls.append(task)
        cards = [{"name": "Web card", "modality": "text", "use_when": "w", "recipe": "r", "watch_out": "o",
                  "source": "https://scikit-learn.org/stable/"}]
        (run_dir / "model_cards.json").write_text(json.dumps({"cards": cards}))
        return cards

    llm = ScriptedLLM()
    c = make_controller(tmp_path, make_cfg(budget={"max_nodes": 3}), llm=llm, retrieve=retrieve)
    c.run()
    assert calls == ["toy-task"]
    assert "Web card" in llm.prompts[0] and "Web card" in llm.prompts[1]

    def never(*args):
        """Fails the test if retrieval runs again."""
        raise AssertionError("retrieval ran again after resume")

    cfg = make_cfg(budget={"max_nodes": 4})
    (tmp_path / "run" / "config.yaml").write_text(__import__("yaml").safe_dump(cfg))
    llm2 = ScriptedLLM()
    resumed = Controller.resume(tmp_path / "run", llm=llm2, sandbox=FakeSandbox(), evaluator=FakeEvaluator(),
                                retrieve=never)
    resumed.done = False
    resumed.run()
    assert "Web card" in llm2.prompts[0]


class FlakyLLM(ScriptedLLM):
    """A ScriptedLLM whose API is down for the calls numbered in `down` (1-based), or for every call."""

    def __init__(self, down: set[int] | None = None, always: bool = False):
        """`down`: which calls fail; `always`: every call fails."""
        super().__init__()
        self.down, self.always, self.calls = down or set(), always, 0

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        """Fail like an unreachable API, or reply as ScriptedLLM does."""
        self.calls += 1
        if self.always or self.calls in self.down:
            raise LLMUnavailable("APIConnectionError: Connection error.")
        return super().__call__(agent=agent, system=system, user=user)


def test_llm_outage_waits_and_records_no_node(tmp_path: Path):
    """Failed LLM calls leave no node behind; the controller waits longer each time and then carries on."""
    llm = FlakyLLM(down={2, 3})
    c = make_controller(tmp_path, make_cfg(budget={"max_nodes": 3}), llm=llm)
    waits = []
    c._sleep = waits.append
    tree = c.run()

    assert list(tree.nodes) == ["n0", "n1", "n2"] and statuses(tree) == ["working"] * 3
    assert waits == [30, 60]
    errors = [json.loads(line) for line in (c.run_dir / "llm_errors.jsonl").read_text().splitlines()]
    assert [e["failures_in_a_row"] for e in errors] == [1, 2] and errors[0]["during"] == "node"
    assert len(list((c.run_dir / "nodes" / "_unfinished").iterdir())) == 2


def test_llm_outage_stops_resumably(tmp_path: Path):
    """After `outage_retries` failures in a row the run stops unfinished, and --resume completes it."""
    cfg = make_cfg(budget={"max_nodes": 3})
    cfg["llm"].update({"outage_retries": 2, "outage_wait_s": 1})
    first = make_controller(tmp_path, cfg, llm=FlakyLLM(down={2, 3}))
    first._sleep = lambda s: None
    with pytest.raises(LLMUnavailable):
        first.run()
    status = latest_complete_checkpoint(first.run_dir)["status"]
    assert status["stop_reason"] == "llm_unavailable" and status["done"] is False
    assert list(latest_complete_checkpoint(first.run_dir)["tree"]["nodes"]) == ["n0"]

    resumed = Controller.resume(first.run_dir, llm=ScriptedLLM(), sandbox=FakeSandbox(), evaluator=FakeEvaluator())
    assert list(resumed.run().nodes) == ["n0", "n1", "n2"]
    assert latest_complete_checkpoint(first.run_dir)["status"]["done"] is True


def test_redirect_survives_an_outage(tmp_path: Path):
    """A redirect pending when the LLM fails is still applied on the next attempt."""
    c = make_controller(tmp_path, make_cfg(budget={"max_nodes": 2}, search={"num_drafts": 1}), llm=FlakyLLM(down={2}))
    c._sleep = lambda s: None

    def redirect_once(llm, tree, findings, run_dir):
        """After the first node, queue a redirect to a new draft, as an applied intervention would."""
        if len(tree.nodes) == 1:
            c.state.forced_next = {"operator": "draft", "parent_id": None}
        return findings

    c.reflect = redirect_once
    tree = c.run()
    assert [n.operator.value for n in tree.nodes.values()] == ["draft", "draft"]  # not an improve of n0


def test_improve_prompt_lists_approaches_from_other_branches(tmp_path: Path):
    """Improving the best draft shows the other draft's approach, so switching to it is not mistaken for new."""
    llm = ScriptedLLM()
    cfg = make_cfg(budget={"max_nodes": 3}, search={"num_drafts": 2, "debug_prob": 0.0})
    c = make_controller(tmp_path, cfg, llm=llm, evaluator=FakeEvaluator([0.5, 0.4]))
    tree = c.run()
    assert tree.nodes["n2"].parent_id == "n1"
    assert "Other branches of this run" in llm.prompts[2]
    assert "- Attempt 1. -> validation 0.5000" in llm.prompts[2]
    assert "- Attempt 2. ->" not in llm.prompts[2]  # the script being improved is not "another branch"


def test_machine_is_recorded_on_start_and_resume(tmp_path: Path, monkeypatch):
    """Each start and resume appends where it ran, so runs can be compared on the same kind of machine."""
    monkeypatch.delenv("COLAB_RELEASE_TAG", raising=False)
    monkeypatch.delenv("COLAB_GPU", raising=False)
    monkeypatch.setenv("KAGGLE_KERNEL_RUN_TYPE", "Batch")
    assert machine_info()["platform"] == "kaggle" and machine_info()["cpus"] >= 1

    c = make_controller(tmp_path, make_cfg(budget={"max_nodes": 1}))
    c.run()
    cfg = make_cfg(budget={"max_nodes": 2})
    (c.run_dir / "config.yaml").write_text(__import__("yaml").safe_dump(cfg))
    resumed = Controller.resume(c.run_dir, llm=ScriptedLLM(), sandbox=FakeSandbox(), evaluator=FakeEvaluator())
    resumed.done = False
    resumed.run()
    records = [json.loads(line) for line in (c.run_dir / "machine.jsonl").read_text().splitlines()]
    assert [r["event"] for r in records] == ["start", "resume"]
    assert records[0]["platform"] == "kaggle" and records[1]["step"] > 0


def test_raise_budget_continues_a_finished_run(tmp_path: Path):
    """A run that ran out of time continues from its checkpoint with more budget, once, and re-picks its final node."""
    c = make_controller(tmp_path, make_cfg(budget={"wall_clock_s": 0, "max_nodes": 3}))
    c.run()
    assert c.done and checkpoint.read(c.run_dir)["status"]["stop_reason"] == "budget" and not c.tree.nodes

    resumed = Controller.resume(c.run_dir, llm=ScriptedLLM(), sandbox=FakeSandbox(), evaluator=FakeEvaluator())
    assert resumed.raise_budget(3600) and not resumed.done
    assert not resumed.raise_budget(3600) and resumed.state.extra_budget_s == 3600  # asking again adds nothing
    tree = resumed.run()
    status = checkpoint.read(c.run_dir)["status"]
    assert len(tree.nodes) == 3 and status["done"] and status["stop_reason"] == "max_nodes"
    assert status["final_node"] in tree.nodes
    events = [json.loads(line)["event"] for line in (c.run_dir / "machine.jsonl").read_text().splitlines()]
    assert events == ["start", "extend", "resume"]

    full = Controller.resume(c.run_dir, llm=ScriptedLLM(), sandbox=FakeSandbox(), evaluator=FakeEvaluator())
    with pytest.raises(ValueError, match="max_nodes"):
        full.raise_budget(7200)


def test_prompts_state_the_configured_limits(tmp_path: Path):
    """Every operator's prompt states sandbox.cpus and sandbox.memory_gb from the config."""
    sandbox = FakeSandbox([Exec(exit_code=1, stderr="boom")])
    cfg = make_cfg(budget={"max_nodes": 3}, search={"num_drafts": 1, "debug_prob": 1.0})
    cfg["sandbox"].update({"cpus": 4, "memory_gb": 8})
    llm = ScriptedLLM()
    make_controller(tmp_path, cfg, llm=llm, sandbox=sandbox).run()

    assert len(llm.prompts) == 3  # draft, debug, improve
    for prompt in llm.prompts:
        assert "CPU only, 4 cores and 8 GB of memory. A script that exceeds the memory limit is killed." in prompt


def test_a_killed_script_is_reported_as_out_of_memory(tmp_path: Path):
    """Exit code 137 without a timeout is recorded as a likely memory kill, and the debug prompt says so."""
    sandbox = FakeSandbox([Exec(exit_code=137), Exec(exit_code=-9, stderr="partial output")])
    cfg = make_cfg(budget={"max_nodes": 3}, search={"num_drafts": 1, "debug_prob": 1.0})
    llm = ScriptedLLM()
    tree = make_controller(tmp_path, cfg, llm=llm, sandbox=sandbox).run()

    n0, n1 = tree.nodes["n0"], tree.nodes["n1"]
    assert n0.error.startswith("runtime_error: exit code 137 (killed, most likely out of memory: the limit is 4 GB)")
    assert n1.error.startswith("runtime_error: exit code -9 (killed") and "partial output" in n1.error
    assert "most likely out of memory: the limit is 4 GB" in llm.prompts[1]


def test_improve_with_identical_predictions_is_marked_as_no_effect(tmp_path: Path):
    """An improve that wrote the same predictions as its parent is shown as having had no effect."""
    cfg = make_cfg(budget={"max_nodes": 3}, search={"num_drafts": 1, "debug_prob": 0.0})
    llm = ScriptedLLM()
    c = make_controller(tmp_path, cfg, llm=llm, sandbox=FakeSandbox(same_predictions=True),
                        evaluator=FakeEvaluator([0.5, 0.5]))
    c.run()

    assert "- Attempt 2. -> no effect: predictions identical to this script's" in llm.prompts[2]
