from dataclasses import dataclass
from pathlib import Path

import pytest

from imle.agents import coding, retrieval


@dataclass
class Ctx:
    """Stand-in for the evaluator's TaskContext."""

    input_dir: Path
    description: str = "Predict y."
    prediction_format: str = "Columns id,y; one row per row of predict.csv."
    metric: str = "rmse"
    higher_is_better: bool = False


@pytest.fixture
def ctx(tmp_path: Path) -> Ctx:
    """A context whose input folder has a small train.csv, predict.csv and an image folder."""
    (tmp_path / "train.csv").write_text("id,y\n1,0.0\n2,1.0\n")
    (tmp_path / "predict.csv").write_text("id\n3\n4\n")
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "a.png").write_bytes(b"")
    return Ctx(input_dir=tmp_path)


def test_parse_response():
    """A reply splits into plan and script; an unclosed code block or empty reply is rejected."""
    plan, script = coding.parse_response("PLAN: Fit a model.\n\n```python\nprint(1)\n```\ntrailing")
    assert plan == "Fit a model." and script == "print(1)\n"
    with pytest.raises(coding.CodingError, match="no complete"):
        coding.parse_response("PLAN: cut off\n```python\nprint(1)")
    with pytest.raises(coding.CodingError, match="empty"):
        coding.parse_response("  ")


def test_with_output_dir_respects_future_imports():
    """OUTPUT_DIR goes first, except that `from __future__` imports must stay at the top."""
    assert coding.with_output_dir("print(1)\n", "/output") == "OUTPUT_DIR = '/output'  # set by the controller\nprint(1)\n"
    script = '"""Doc."""\nfrom __future__ import annotations\nimport os\n'
    out = coding.with_output_dir(script, "/output")
    assert out.index("from __future__") < out.index("OUTPUT_DIR") < out.index("import os")
    compile(out, "solution.py", "exec")


def test_with_output_dir_disables_the_scripts_own_assignments(tmp_path: Path):
    """A script that sets OUTPUT_DIR itself still writes where the controller says."""
    script = (
        'OUTPUT_DIR = "/kaggle/working"\n'
        "import os\n"
        'OUTPUT_DIR = os.environ.get(\n    "OUTPUT_DIR", ".")\n'
        "if True:\n"
        '    OUTPUT_DIR: str = "elsewhere"\n'
        "def f():\n"
        '    OUTPUT_DIR = "local"  # a function\'s own variable, left alone\n'
        "    return OUTPUT_DIR\n"
        'open(os.path.join(OUTPUT_DIR, "predictions.csv"), "w").write(f())\n'
    )
    out = coding.with_output_dir(script, str(tmp_path))
    exec(compile(out, "solution.py", "exec"), {})  # noqa: S102 - our own test script
    assert (tmp_path / "predictions.csv").read_text() == "local"
    assert out.count("this line was:") == 3
    assert out.splitlines()[1] == "pass  # OUTPUT_DIR is set by the controller; this line was: OUTPUT_DIR = \"/kaggle/working\""
    assert len(out.splitlines()) == len(script.splitlines()) + 1  # line numbers in tracebacks shift by one only


def test_with_output_dir_leaves_unparsable_scripts_alone():
    """A script with a syntax error runs as written, so the error the model sees is its own."""
    script = 'OUTPUT_DIR = "x"\ndef broken(:\n'
    assert coding.with_output_dir(script, "/output") == "OUTPUT_DIR = '/output'  # set by the controller\n" + script


def test_draft_prompt_shows_data_contract_and_memory(ctx: Ctx):
    """The draft prompt carries the data preview, output contract, metric, timeout, memory and past plans."""
    findings = [{"id": "f1", "text": "char n-grams help", "evidence": [{"node_id": "n3", "val_score": 0.41}]}]
    prompt = coding.draft_prompt(
        ctx, timeout_s=600, findings=findings, cards=retrieval.cards_for("spooky-author-identification"),
        previous_plans=["Logistic regression on word counts."],
    )
    assert "input/train.csv" in prompt and "id,y" in prompt and "input/images/ (1 entries, e.g. a.png)" in prompt
    assert 'os.path.join(OUTPUT_DIR, "predictions.csv")' in prompt and ctx.prediction_format in prompt
    assert "rmse (lower is better)" in prompt and "600 seconds" in prompt
    assert "[f1] char n-grams help (evidence: n3=0.41)" in prompt
    assert prompt.count("<model_cards>") == 1 and "Naive Bayes on counts" in prompt
    assert "- Logistic regression on word counts." in prompt


def test_debug_and_improve_generate(ctx: Ctx):
    """debug and improve send their own prompts and return the parsed plan and script."""
    prompts = []

    def llm(*, agent, system, user):
        """Record the prompt and reply with a fixed script."""
        prompts.append(user)
        return "PLAN: Fixed.\n```python\nprint(2)\n```"

    assert coding.debug(llm, ctx, 60, "print(1)", "runtime_error: boom") == ("Fixed.", "print(2)\n")
    assert coding.improve(llm, ctx, 60, "print(1)", "Mean.", 0.3, "x" * 5000) == ("Fixed.", "print(2)\n")
    assert "runtime_error: boom" in prompts[0] and "Fix the problem" in prompts[0]
    assert "It scores 0.3" in prompts[1] and "[... earlier output cut ...]" in prompts[1]


def test_retry_once_on_bad_reply(ctx: Ctx):
    """A reply without a script is retried once before giving up."""
    replies = iter(["sorry", "PLAN: ok\n```python\npass\n```"])
    assert coding.draft(lambda **kw: next(replies), ctx, 60) == ("ok", "pass\n")
    with pytest.raises(coding.CodingError):
        coding.draft(lambda **kw: "sorry", ctx, 60)


def test_cards_cover_every_task():
    """Every project task has at least one card, every card has the full schema, unknown tasks get none."""
    fields = {"name", "modality", "use_when", "recipe", "watch_out"}
    assert all(set(card) == fields for card in retrieval.CARDS)
    assert all(retrieval.cards_for(task) for task in retrieval.TASK_MODALITIES)
    assert retrieval.cards_for("unknown-task") == []
