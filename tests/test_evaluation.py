"""Stage 2: A1's frozen harness, scoring and leakage screen."""

import json
import math
import textwrap
from pathlib import Path

import pytest
import yaml
from conftest import SPOOKY, uniform_predictions

from imle.agents import evaluation as a1
from imle.agents.reflection import StructuredOutputError


class ScriptedLLM:
    """Returns canned replies in order and records the prompts."""

    def __init__(self, *replies: str):
        self.replies = list(replies)
        self.prompts: list[str] = []

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        self.prompts.append(user)
        return self.replies.pop(0)


def prepared_run(tmp_path: Path, agents: dict | None = None) -> tuple[Path, object]:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "config.yaml").write_text(yaml.safe_dump({"agents": agents or {}, "splits": {"probe_fraction": 0.1}}))
    return run_dir, a1.prepare(SPOOKY, run_dir, seed=0)


def node_with(run_dir: Path, ctx, node_id: str = "n0", seed: int | None = None) -> Path:
    node_dir = run_dir / "nodes" / node_id
    (node_dir / "output").mkdir(parents=True)
    uniform_predictions(Path(ctx.input_dir), seed).to_csv(node_dir / "output" / "predictions.csv", index=False)
    return node_dir


# --------------------------------------------------------------------------- harness


def test_prepare_freezes_harness(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepared_run(tmp_path)
    spec = a1.verify(run_dir)
    assert spec["task"] == SPOOKY and spec["rows"]["probe"] == 6 and spec["rows"]["val"] == 12
    assert set(spec["files"]) >= {"stand_in/harness/labels.csv", "stand_in/harness/meta.json"}
    assert all(not ((run_dir / f).stat().st_mode & 0o222) for f in spec["files"])
    assert ctx.metric == "multi-class log loss" and ctx.higher_is_better is False
    # The harness is outside the input folder A3's scripts see.
    visible = {str(p.relative_to(ctx.input_dir)) for p in Path(ctx.input_dir).rglob("*")}
    assert visible == {"train.csv", "predict.csv"}


def test_prepare_again_returns_frozen_context_without_rebuilding(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepared_run(tmp_path)
    before = (run_dir / "a1" / "harness.sha256").read_text()
    again = a1.prepare(SPOOKY, run_dir, seed=0)
    assert vars(again) == vars(ctx)
    assert (run_dir / "a1" / "harness.sha256").read_text() == before


def test_freeze_refuses_regeneration(tmp_path: Path, spooky_data: Path):
    run_dir, _ = prepared_run(tmp_path)
    with pytest.raises(a1.HarnessIntegrityError, match="never regenerated"):
        a1.freeze(run_dir, {"task": SPOOKY}, {})


def test_score_matches_known_value(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepared_run(tmp_path)
    result = a1.score(node_with(run_dir, ctx))
    assert result.error is None
    assert result.val_score == pytest.approx(math.log(3)) and result.probe_score == pytest.approx(math.log(3))
    assert (run_dir / "nodes" / "n0" / "submission.csv").exists()


def test_score_refuses_tampered_harness(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepared_run(tmp_path)
    labels = run_dir / "stand_in" / "harness" / "labels.csv"
    labels.chmod(0o644)
    labels.write_text(labels.read_text().replace("EAP", "HPL"))
    result = a1.score(node_with(run_dir, ctx))
    assert result.val_score is None and result.error.startswith("harness_integrity: harness files changed")
    with pytest.raises(a1.HarnessIntegrityError):
        a1.prepare(SPOOKY, run_dir, seed=0)


def test_score_refuses_edited_spec(tmp_path: Path, spooky_data: Path):
    run_dir, ctx = prepared_run(tmp_path)
    spec_path = run_dir / "a1" / "harness.json"
    spec = json.loads(spec_path.read_text())
    spec["higher_is_better"] = True
    spec_path.write_text(json.dumps(spec))
    assert "does not match" in a1.score(node_with(run_dir, ctx)).error


def test_score_reports_missing_predictions(tmp_path: Path, spooky_data: Path):
    run_dir, _ = prepared_run(tmp_path)
    (run_dir / "nodes" / "n0" / "output").mkdir(parents=True)
    assert a1.score(run_dir / "nodes" / "n0").error == "predictions.csv not found"


# --------------------------------------------------------------------------- leakage rules


def flags(script: str, **meta) -> list[str]:
    return [f.rule for f in a1.screen_script(textwrap.dedent(script), task_meta=meta or None).flags]


HEADER = """\
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
train = pd.read_csv("input/train.csv")
test = pd.read_csv("input/predict.csv")
y = train["author"]
"""


@pytest.mark.parametrize("script", [
    HEADER + "X = train\nLogisticRegression().fit(X, y)\n",
    HEADER + "X = train.drop(columns=['id'])\nm = LogisticRegression()\nm.fit(X, y)\n",
    HEADER + "feats = ['len', 'author']\nLogisticRegression().fit(train[feats], y)\n",
    HEADER + "X = train.copy().fillna(0).values\nLogisticRegression().fit(X, y)\n",
])
def test_r1_target_as_feature(script: str):
    assert flags(script) == ["R1_target_as_feature"]


@pytest.mark.parametrize("script", [
    HEADER + "X = train.drop(columns=['id', 'author'])\nLogisticRegression().fit(X, y)\n",
    HEADER + "X = train.drop('author', axis=1)\nLogisticRegression().fit(X, y)\n",
    HEADER + "feats = [c for c in train.columns if c != 'author']\nLogisticRegression().fit(train[feats], y)\n",
    HEADER + "X = train[['len', 'n_words']]\nLogisticRegression().fit(X, y)\n",
])
def test_r1_clean(script: str):
    assert flags(script) == []


def test_r1_uses_task_meta_target():
    script = "import pandas as pd\nd = pd.read_csv('input/train.csv')\nm.fit(d, d['Insult'])\n"
    assert flags(script, target="Insult") == ["R1_target_as_feature"]


def test_r2_test_statistics_is_a_warning():
    script = HEADER + "full = pd.concat([train, test])\nfull['len'] = full['len'].fillna(full['len'].mean())\n"
    report = a1.screen_script(script)
    assert [f.rule for f in report.flags] == ["R2_test_statistics"] and report.verdict == "warn"
    assert a1.screen(None, script) is None  # a warning does not reject the script


def test_r2_transformer_fitted_on_predict_rows():
    script = HEADER + "vec.fit(pd.concat([train['text'], test['text']]))\n"
    assert flags(script) == ["R2_test_statistics"]


def test_r2_ignores_statistics_of_predictions():
    script = HEADER + ("m = LogisticRegression().fit(train[['len']], y)\np = m.predict_proba(test[['len']])\n"
                       "print(p.max(axis=1))\ntrain['len'] = train['len'].fillna(train['len'].median())\n")
    assert flags(script) == []


def test_r3_val_rows_in_training():
    script = HEADER + textwrap.dedent("""\
        X_tr, X_va, y_tr, y_va = train_test_split(train[['len']], y, test_size=0.2)
        m = LogisticRegression()
        m.fit(pd.concat([X_tr, X_va]), pd.concat([y_tr, y_va]))
        print(m.score(X_va, y_va))
        """)
    assert flags(script) == ["R3_val_in_training"]


def test_r3_refit_on_all_rows_after_validating_is_clean():
    script = HEADER + textwrap.dedent("""\
        X_tr, X_va, y_tr, y_va = train_test_split(train[['len']], y, test_size=0.2)
        m = LogisticRegression()
        m.fit(X_tr, y_tr)
        print(m.score(X_va, y_va))
        m.fit(pd.concat([X_tr, X_va]), pd.concat([y_tr, y_va]))
        p = m.predict_proba(test[['len']])
        """)
    assert flags(script) == []


@pytest.mark.parametrize("path", ["../stand_in/harness/labels.csv", "/root/.cache/mle-bench/data/x.csv",
                                  "../../private/test.csv"])
def test_r0_harness_access(path: str):
    script = f"import pandas as pd\nlabels = pd.read_csv({path!r})\n"
    report = a1.screen_script(script)
    assert report.verdict == "leak" and report.flags[0].rule == "R0_harness_access"
    assert a1.screen(None, script).startswith("R0_harness_access (line 2)")


def test_r0_parent_walk_and_clean_strings():
    assert flags("from pathlib import Path\np = Path(__file__).resolve().parent.parent\n") == ["R0_harness_access"]
    assert flags("print('Loading...')\nopen('input/train.csv')\nprint('see ../harness')\n") == []


def test_unparseable_script_gets_no_flags():
    assert a1.screen_script("def broken(:\n").verdict == "clean"


# --------------------------------------------------------------------------- LLM review


def test_llm_review_adds_flag_after_retry():
    llm = ScriptedLLM("not json", '{"leak": true, "kind": "target_as_feature", "line": 3, "reason": "uses author"}')
    report = a1.screen_script(HEADER, llm=llm)
    assert report.verdict == "leak" and report.flags[-1].source == "llm"
    assert len(llm.prompts) == 2 and "not valid" in llm.prompts[1]


def test_llm_review_clean_reply_adds_nothing():
    llm = ScriptedLLM('```json\n{"leak": false, "kind": "none", "line": null, "reason": "fine"}\n```')
    assert a1.screen_script(HEADER, llm=llm).verdict == "clean"


def test_llm_review_fails_clearly_after_retries():
    llm = ScriptedLLM("no", "still no", '{"leak": "maybe"}')
    with pytest.raises(StructuredOutputError, match="3 attempts"):
        a1.screen_script(HEADER, llm=llm, max_retries=2)
