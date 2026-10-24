"""Stage 4: the A1-off and A4-off switches, through A1 directly and through the real controller."""

import json
import math
from pathlib import Path

import pandas as pd
import pytest
import yaml
from conftest import SPOOKY, uniform_predictions

from imle import checkpoint
from imle.agents import evaluation as a1
from imle.agents import reflection as a4


def prepare(tmp_path: Path, evaluation: bool):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "config.yaml").write_text(yaml.safe_dump({"agents": {"evaluation": evaluation}}))
    return run_dir, a1.prepare(SPOOKY, run_dir, seed=0)


def labels(run_dir: Path) -> pd.DataFrame:
    return pd.read_csv(run_dir / "stand_in" / "harness" / "labels.csv")


def test_a1_on_keeps_validation_external(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepare(tmp_path, evaluation=True)
    assert a1.verify(run_dir)["mode"] == "harness"
    assert "val_score.json" not in ctx.prediction_format
    assert len(pd.read_csv(Path(ctx.input_dir) / "train.csv")) == 42
    assert set(labels(run_dir)["split"]) == {"val", "probe", "test"}


def test_a1_off_moves_validation_into_train_and_keeps_probe(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepare(tmp_path, evaluation=False)
    assert a1.verify(run_dir)["mode"] == "self_report"
    assert "val_score.json" in ctx.prediction_format and "multi-class log loss" in ctx.prediction_format
    train = pd.read_csv(Path(ctx.input_dir) / "train.csv")
    predict = pd.read_csv(Path(ctx.input_dir) / "predict.csv")
    assert len(train) == 54 and list(train.columns) == ["id", "text", "author"] and train["author"].notna().all()
    assert set(labels(run_dir)["split"]) == {"probe", "test"}
    assert set(predict["id"]) == set(labels(run_dir)["id"])   # probe and test rows only
    assert not set(train["id"]) & set(predict["id"])


def test_a1_off_split_is_the_a1_on_split(tmp_path: Path, spooky_data: Path):
    """The probe rows are the same in both modes, so the probe compares conditions fairly."""
    on_dir, _ = prepare(tmp_path / "on", evaluation=True)
    off_dir, _ = prepare(tmp_path / "off", evaluation=False)
    probe = [set(labels(d).query("split == 'probe'")["id"]) for d in (on_dir, off_dir)]
    assert probe[0] == probe[1] and len(probe[0]) == 6


def write_node(run_dir: Path, ctx, report: object | None) -> Path:
    node_dir = run_dir / "nodes" / "n0"
    (node_dir / "output").mkdir(parents=True)
    uniform_predictions(Path(ctx.input_dir)).to_csv(node_dir / "output" / "predictions.csv", index=False)
    if report is not None:
        (node_dir / "output" / "val_score.json").write_text(json.dumps(report))
    return node_dir


def test_a1_off_takes_validation_from_the_script(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepare(tmp_path, evaluation=False)
    result = a1.score(write_node(run_dir, ctx, {"val_score": 0.123}))
    assert result.error is None and result.val_score == 0.123
    assert result.probe_score == pytest.approx(math.log(3)) and result.test_score == pytest.approx(math.log(3))
    assert len(pd.read_csv(run_dir / "nodes" / "n0" / "submission.csv")) == 9


@pytest.mark.parametrize("report, message", [
    (None, "val_score.json not found"),
    ({"score": 1}, "val_score.json is invalid"),
    ({"val_score": "nan"}, "not a finite number"),
])
def test_a1_off_rejects_missing_or_bad_self_report(tmp_path: Path, spooky_data: Path, report, message):
    run_dir, ctx = prepare(tmp_path, evaluation=False)
    result = a1.score(write_node(run_dir, ctx, report))
    assert result.val_score is None and message in result.error


# --------------------------------------------------------------------------- through the controller


class PredictingSandbox:
    """Writes uniform predictions for predict.csv in the workspace, and a self-reported score."""

    def output_path(self, output_dir: Path) -> str:
        return str(output_dir)

    def run(self, script_path: Path, workspace: Path, output_dir: Path, timeout_s: float):
        from test_controller import Exec

        uniform_predictions(workspace / "input").to_csv(output_dir / "predictions.csv", index=False)
        (output_dir / "val_score.json").write_text('{"val_score": 0.5}')
        return Exec()


class RecordingLLM:
    def __init__(self):
        self.agents: list[str] = []
        self.prompts: list[str] = []

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        from test_controller import reply

        self.agents.append(agent)
        self.prompts.append(user)
        if agent == "reflection":
            return json.dumps({"findings": [{"text": "Uniform predictions give ln 3.", "effect": "neutral",
                                             "evidence": ["n0"]}]})
        return reply(f"Attempt {len(self.prompts)}.")


def run_condition(tmp_path: Path, condition: str) -> tuple[Path, RecordingLLM]:
    from test_controller import REPO

    from imle.controller import Controller, load_config

    cfg = load_config(REPO / "configs" / "conditions" / condition)
    cfg["budget"].update({"max_nodes": 3})
    cfg["search"].update({"num_drafts": 2})
    cfg["retrieval"]["source"] = "static"
    llm = RecordingLLM()
    Controller(cfg, SPOOKY, 0, tmp_path / "run", llm=llm, sandbox=PredictingSandbox(), evaluator=a1,
               reflect=a4.reflect).run()
    return tmp_path / "run", llm


def test_controller_c1_scores_with_the_harness_and_reflects(tmp_path: Path, spooky_data: Path):
    run_dir, llm = run_condition(tmp_path, "c1_autonomous.yaml")
    ck = checkpoint.read(run_dir)
    nodes = ck["tree"]["nodes"]
    assert all(n["status"] == "working" for n in nodes.values())
    assert nodes["n0"]["val_score"] == pytest.approx(math.log(3))   # the harness, not the self-report
    assert "reflection" in llm.agents and len(ck["findings"]) == 1


def test_controller_a1_off_uses_self_report_and_skips_screen(tmp_path: Path, spooky_data: Path, monkeypatch):
    monkeypatch.setattr(a1, "screen", lambda llm, script: pytest.fail("screen must not run with A1 off"))
    run_dir, llm = run_condition(tmp_path, "ablation_a1_off.yaml")
    nodes = checkpoint.read(run_dir)["tree"]["nodes"]
    assert {n["val_score"] for n in nodes.values()} == {0.5}
    assert all(n["probe_score"] == pytest.approx(math.log(3)) for n in nodes.values())
    assert "val_score.json" in llm.prompts[0]


def test_controller_a4_off_never_reflects(tmp_path: Path, spooky_data: Path):
    run_dir, llm = run_condition(tmp_path, "ablation_a4_off.yaml")
    assert "reflection" not in llm.agents
    assert checkpoint.read(run_dir)["findings"] == []
    assert not (run_dir / "a4").exists()
