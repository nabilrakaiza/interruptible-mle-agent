import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from imle import checkpoint
from imle.agents import coding
from imle.controller import Controller, load_config, select_next
from imle.tree import Node, NodeStatus, Operator, Tree

REPO = Path(__file__).resolve().parents[1]

SCRIPT = """\
import pandas as pd
train = pd.read_csv("input/train.csv")
predict = pd.read_csv("input/predict.csv")
predict.assign(y=train["y"].mean()).to_csv("predictions.csv", index=False)
"""
REPLY = f"PLAN: Predict the training mean.\n\n```python\n{SCRIPT}```\n"


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
    """Scores nodes from a fixed list instead of reading predictions."""

    def __init__(self, scores: list[Score]):
        """`scores` are handed out one per scored node, in order."""
        self.scores = iter(scores)

    def prepare(self, task: str, run_dir: Path, seed: int) -> Ctx:
        """Write a two-row train.csv and predict.csv under the run folder."""
        input_dir = run_dir / "input"
        input_dir.mkdir()
        (input_dir / "train.csv").write_text("id,y\n1,0.0\n2,1.0\n")
        (input_dir / "predict.csv").write_text("id\n3\n4\n")
        return Ctx(input_dir=input_dir)

    def score(self, node_dir: Path) -> Score:
        """Return the next canned score, writing submission.csv unless it is an error."""
        s = next(self.scores)
        if s.error is None:
            (node_dir / "submission.csv").write_text(f"id,y\n4,{s.val_score}\n")
        return s


def fake_llm(*, agent: str, system: str, user: str) -> str:
    """An LLM that always replies with the same valid plan and script."""
    return REPLY


def subprocess_run(script_path: Path, cwd: Path, timeout_s: float) -> Exec:
    """A sandbox that really executes the script, as a plain subprocess."""
    p = subprocess.run(
        [sys.executable, script_path.name], cwd=cwd, capture_output=True, text=True, timeout=timeout_s, check=False
    )
    return Exec(stdout=p.stdout, stderr=p.stderr, exit_code=p.returncode)


def make_cfg(**budget) -> dict:
    """The C1 config, with any `budget` settings overridden."""
    cfg = load_config(REPO / "configs" / "conditions" / "c1_autonomous.yaml")
    cfg["budget"].update(budget)
    return cfg


def make_controller(tmp_path: Path, cfg: dict, scores: list[Score], sandbox_run=None, llm=fake_llm) -> Controller:
    """A controller on fakes. By default every script exits cleanly without running."""
    return Controller(
        cfg,
        "toy-task",
        0,
        tmp_path / "run",
        llm=llm,
        sandbox_run=sandbox_run or (lambda script_path, cwd, timeout_s: Exec()),
        evaluator=FakeEvaluator(scores),
    )


def test_load_config_merges_and_expands(monkeypatch):
    """A condition file overrides base.yaml key by key, and ${LLM_MODEL} is filled in."""
    monkeypatch.setenv("LLM_MODEL", "some-model")
    cfg = load_config(REPO / "configs" / "conditions" / "ablation_a4_off.yaml")
    assert cfg["condition"] == "A4-off"
    assert cfg["agents"] == {"evaluation": True, "retrieval": True, "reflection": False}
    assert cfg["llm"]["model"] == "some-model"
    assert cfg["budget"]["max_nodes"] == 200


def test_select_next_drafts_until_num_drafts():
    """Drafts are requested until num_drafts exist, counting buggy ones, then the search ends."""
    cfg = {"search": {"num_drafts": 2}}
    tree = Tree()
    assert select_next(tree, cfg) == (Operator.DRAFT, None)
    tree.add(Node(id="n0", operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=0.5))
    assert select_next(tree, cfg) == (Operator.DRAFT, None)
    tree.add(Node(id="n1", operator=Operator.DRAFT, status=NodeStatus.BUGGY))
    assert select_next(tree, cfg) is None


def test_run_end_to_end_with_real_script(tmp_path: Path):
    """The generated script really runs, in the node directory, against ./input."""
    scores = [Score(val_score=v, probe_score=v + 0.1) for v in (0.9, 0.4, 0.7, 0.6, 0.8)]
    c = make_controller(tmp_path, make_cfg(), scores, sandbox_run=subprocess_run)
    tree = c.run()

    assert [n.status for n in tree.nodes.values()] == [NodeStatus.WORKING] * 5
    assert tree.nodes["n0"].plan == "Predict the training mean."
    assert (c.run_dir / "nodes" / "n0" / "predictions.csv").read_text() == "id,y\n3,0.5\n4,0.5\n"

    # rmse: lower is better, so n1 wins
    assert tree.best_by_val().id == "n1"
    assert (c.run_dir / "submission.csv").read_text() == "id,y\n4,0.4\n"

    # one checkpoint before the first node, one per node, one at the end
    assert checkpoint.latest_step(c.run_dir) == 6
    final = checkpoint.read(c.run_dir)
    assert final["status"]["done"] and final["status"]["final_node"] == "n1"
    assert final["status"]["stop_reason"] == "search_exhausted"
    assert final["tree"]["nodes"]["n1"]["probe_score"] == pytest.approx(0.5)
    assert checkpoint.read(c.run_dir, 0)["tree"]["nodes"] == {}
    assert (c.run_dir / "config.yaml").exists()


def test_failures_become_buggy_nodes(tmp_path: Path):
    """Each failure stage gives a buggy node with its own error category, and the run carries on."""
    results = iter([
        Exec(timed_out=True),
        Exec(exit_code=1, stderr="Traceback ...\nKeyError: 'text'"),
        Exec(),
        Exec(),
    ])
    replies = iter(["no code here", "still no code"] + [REPLY] * 4)
    c = make_controller(
        tmp_path,
        make_cfg(),
        [Score(error="predictions.csv not found"), Score(val_score=0.3)],
        sandbox_run=lambda script_path, cwd, timeout_s: next(results),
        llm=lambda **kw: next(replies),
    )
    nodes = list(c.run().nodes.values())

    assert [n.status for n in nodes] == [NodeStatus.BUGGY] * 4 + [NodeStatus.WORKING]
    assert [n.error.split(":")[0] for n in nodes[:4]] == [
        "generation_error", "timeout", "runtime_error", "invalid_submission",
    ]
    assert "KeyError: 'text'" in nodes[2].error
    assert all(n.val_score is None for n in nodes[:4])
    assert checkpoint.read(c.run_dir)["status"]["final_node"] == "n4"


def test_stops_on_node_cap(tmp_path: Path):
    """The search stops at max_nodes even when more drafts are due."""
    c = make_controller(tmp_path, make_cfg(max_nodes=2), [Score(val_score=0.5), Score(val_score=0.6)])
    assert len(c.run().nodes) == 2
    assert checkpoint.read(c.run_dir)["status"]["stop_reason"] == "max_nodes"


def test_stops_on_budget_without_submission(tmp_path: Path):
    """The search stops when the wall clock runs out, and writes no submission if nothing worked."""
    def slow(script_path, cwd, timeout_s):
        """A sandbox whose script outlasts the whole budget and then fails."""
        time.sleep(0.2)
        return Exec(exit_code=1)

    c = make_controller(tmp_path, make_cfg(wall_clock_s=0.1), [], sandbox_run=slow)
    assert len(c.run().nodes) == 1
    status = checkpoint.read(c.run_dir)["status"]
    assert status["stop_reason"] == "budget" and status["final_node"] is None
    assert not (c.run_dir / "submission.csv").exists()


def test_parse_response():
    """A reply splits into plan and script; an unclosed code block is rejected."""
    plan, script = coding.parse_response("PLAN: Fit a model.\n\n```python\nprint(1)\n```\ntrailing")
    assert plan == "Fit a model." and script == "print(1)\n"
    with pytest.raises(coding.CodingError):
        coding.parse_response("PLAN: cut off\n```python\nprint(1)")


def test_draft_prompt_shows_data_and_contract(tmp_path: Path):
    """The draft prompt carries the data preview, the output contract, the metric and the timeout."""
    ctx = FakeEvaluator([]).prepare("toy-task", tmp_path, 0)
    prompt = coding.draft_prompt(ctx, timeout_s=600)
    assert "input/train.csv" in prompt and "id,y" in prompt
    assert "predictions.csv" in prompt and ctx.prediction_format in prompt
    assert "rmse (lower is better)" in prompt and "600 seconds" in prompt
