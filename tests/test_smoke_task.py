import importlib.util
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("sklearn")

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("smoke_run", ROOT / "scripts" / "smoke_run.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def test_toy_evaluator_scores_and_rejects(tmp_path: Path):
    """Good predictions get log losses and a test submission; malformed ones get an error."""
    ev = smoke.ToyEvaluator()
    ctx = ev.prepare(smoke.TASK, tmp_path, 0)
    train, predict = pd.read_csv(ctx.input_dir / "train.csv"), pd.read_csv(ctx.input_dir / "predict.csv")
    assert "target" in train and "target" not in predict and "split" not in predict
    assert len(train) + len(predict) == 569

    node = tmp_path / "nodes" / "n0"
    (node / "output").mkdir(parents=True)
    predict.assign(target=0.5)[["id", "target"]].to_csv(node / "output" / "predictions.csv", index=False)
    score = ev.score(node)
    assert score.error is None and score.val_score == pytest.approx(0.6931, abs=1e-3)
    assert len(pd.read_csv(node / "submission.csv")) == len(predict) - 85 - 56  # test rows only

    predict.assign(target=2.0)[["id", "target"]].to_csv(node / "output" / "predictions.csv", index=False)
    assert "probability" in ev.score(node).error
    (node / "output" / "predictions.csv").unlink()
    assert ev.score(node).error == "predictions.csv not found"


def test_canned_replies_parse():
    """Dry-run replies are well-formed, so a dry run exercises the whole loop."""
    from imle.agents.coding import parse_response

    plan, script = parse_response(smoke.CannedLLM()(agent="coding", system="", user=""))
    assert plan.startswith("Scaled logistic regression") and "OUTPUT_DIR" in script
