import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from imle import stand_in_evaluation as ev
from imle.controller import Controller, load_config
from imle.execution import SubprocessSandbox

pytest.importorskip("sklearn")

REPO = Path(__file__).resolve().parents[1]
SPOOKY = "spooky-author-identification"
NOMAD = "nomad2018-predict-transparent-conductors"
CACTUS = "aerial-cactus-identification"
AUTHORS = ["EAP", "HPL", "MWS"]


def fake_data(root: Path) -> None:
    """A tiny MLE-bench data folder with spooky, nomad and cactus, in MLE-bench's prepared layout."""
    rng = np.random.default_rng(0)
    pub, priv = root / SPOOKY / "prepared" / "public", root / SPOOKY / "prepared" / "private"
    pub.mkdir(parents=True)
    priv.mkdir(parents=True)
    authors = [AUTHORS[i % 3] for i in range(60)]
    pd.DataFrame({"id": [f"id{i:03}" for i in range(60)], "text": [f"text {a}" for a in authors],
                  "author": authors}).to_csv(pub / "train.csv", index=False)
    pd.DataFrame({"id": [f"t{i}" for i in range(9)], "text": "x"}).to_csv(pub / "test.csv", index=False)
    answers = pd.DataFrame({"id": [f"t{i}" for i in range(9)]})
    for j, a in enumerate(AUTHORS):
        answers[a] = [int(i % 3 == j) for i in range(9)]
    answers.to_csv(priv / "test.csv", index=False)
    (pub / "description.md").write_text("# Overview\n\nGuess the author.")

    pub, priv = root / NOMAD / "prepared" / "public", root / NOMAD / "prepared" / "private"
    targets = ["formation_energy_ev_natom", "bandgap_energy_ev"]
    for name, n in (("train", 40), ("test", 6)):
        df = pd.DataFrame({"id": range(1, n + 1), "spacegroup": 12})
        for i in df["id"]:
            (pub / name / str(i)).mkdir(parents=True)
            (pub / name / str(i) / "geometry.xyz").write_text(f"{name} {i}\n")
        if name == "train":
            df[targets[0]], df[targets[1]] = rng.uniform(0, 1, n), rng.uniform(1, 3, n)
        df.to_csv(pub / f"{name}.csv", index=False)
    priv.mkdir(parents=True)
    test = pd.read_csv(pub / "test.csv")
    test[targets[0]], test[targets[1]] = 0.5, 2.0
    test.to_csv(priv / "test.csv", index=False)
    (pub / "description.md").write_text("# Overview\n\nPredict two energies.")

    pub, priv = root / CACTUS / "prepared" / "public", root / CACTUS / "prepared" / "private"
    pub.mkdir(parents=True)
    priv.mkdir(parents=True)
    train_ids, test_ids = [f"a{i}.jpg" for i in range(30)], [f"b{i}.jpg" for i in range(6)]
    pd.DataFrame({"id": train_ids, "has_cactus": [i % 2 for i in range(30)]}).to_csv(pub / "train.csv", index=False)
    pd.DataFrame({"id": test_ids, "has_cactus": 0.5}).to_csv(pub / "sample_submission.csv", index=False)
    pd.DataFrame({"id": test_ids, "has_cactus": [i % 2 for i in range(6)]}).to_csv(priv / "test.csv", index=False)
    for name, ids in (("train.zip", train_ids), ("test.zip", test_ids)):
        with zipfile.ZipFile(pub / name, "w") as z:
            for i in ids:
                z.writestr(i, b"jpg")
    (pub / "description.md").write_text("# Overview\n\nFind cacti.")


@pytest.fixture
def data(tmp_path: Path, monkeypatch) -> Path:
    """MLEBENCH_DATA_DIR pointed at a fresh fake data folder."""
    root = tmp_path / "mlebench"
    fake_data(root)
    monkeypatch.setenv("MLEBENCH_DATA_DIR", str(root))
    return root


def labels(run: Path) -> pd.DataFrame:
    """The harness labels, ids as text."""
    return pd.read_csv(run / "stand_in" / "harness" / "labels.csv", dtype={"id": str})


def write(run: Path, df: pd.DataFrame, node: str = "n0") -> Path:
    """Write a node's predictions.csv and return the node folder."""
    out = run / "nodes" / node / "output"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "predictions.csv", index=False)
    return out.parent


def test_spooky_splits_scores_and_submission(data: Path, tmp_path: Path):
    """Splits are disjoint and seed-independent; perfect predictions score ~0; the submission is MLE-bench's format."""
    run = tmp_path / "run"
    ctx = ev.prepare(SPOOKY, run, seed=5)
    assert ctx.metric == "multi-class log loss" and not ctx.higher_is_better
    assert "# Files for this run" in ctx.description and "EAP" in ctx.prediction_format
    train, predict = pd.read_csv(ctx.input_dir / "train.csv"), pd.read_csv(ctx.input_dir / "predict.csv")
    assert list(train.columns) == ["id", "text", "author"] and list(predict.columns) == ["id", "text"]
    lab = labels(run)
    assert set(lab["split"]) == {"val", "probe", "test"}
    assert len(train) + (lab.split != "test").sum() == 60 and (lab.split == "test").sum() == 9
    assert not set(train["id"]) & set(predict["id"]) and set(predict["id"]) == set(lab["id"])

    other = tmp_path / "other_seed"
    ev.prepare(SPOOKY, other, seed=99)
    assert pd.read_csv(other / "stand_in" / "input" / "train.csv")["id"].tolist() == train["id"].tolist()

    perfect = pd.DataFrame({"id": lab["id"]})
    for a in AUTHORS:
        perfect[a] = (lab["label"] == a).astype(float)
    result = ev.score(write(run, perfect))
    assert result.error is None
    assert result.val_score < 1e-6 and result.probe_score < 1e-6 and result.test_score < 1e-6
    sub = pd.read_csv(run / "nodes" / "n0" / "submission.csv")
    assert list(sub.columns) == ["id", *AUTHORS] and sub["id"].tolist() == [f"t{i}" for i in range(9)]


def test_rejects_what_mlebench_would_reject(data: Path, tmp_path: Path):
    """Missing ids, rows not summing to one and missing columns are errors, never exceptions."""
    run = tmp_path / "run"
    ev.prepare(SPOOKY, run, seed=0)
    ids = labels(run)["id"]
    uniform = pd.DataFrame({"id": ids, **{a: 1 / 3 for a in AUTHORS}})
    assert ev.score(write(run, uniform)).val_score == pytest.approx(np.log(3))
    assert "ids do not match" in ev.score(write(run, uniform.iloc[1:])).error
    assert "sum to 1" in ev.score(write(run, uniform.assign(EAP=0.9))).error
    assert "missing columns" in ev.score(write(run, uniform.drop(columns="MWS"))).error
    assert ev.score(run / "nodes" / "n9").error == "predictions.csv not found"


def test_nomad_renumbers_ids_and_links_geometry(data: Path, tmp_path: Path):
    """Train and test ids overlap in the original, so every row gets a new id with its geometry file."""
    run = tmp_path / "run"
    ctx = ev.prepare(NOMAD, run, seed=0)
    train, predict = pd.read_csv(ctx.input_dir / "train.csv"), pd.read_csv(ctx.input_dir / "predict.csv")
    ids = list(train["id"]) + list(predict["id"])
    assert sorted(ids) == list(range(1, 47))
    assert all((ctx.input_dir / "geometry" / f"{i}.xyz").exists() for i in ids)
    lab = pd.read_csv(run / "stand_in" / "harness" / "labels.csv")
    first_test = lab[(lab.split == "test") & (lab.position == 0)].iloc[0]
    assert (ctx.input_dir / "geometry" / f"{first_test['id']}.xyz").read_text() == "test 1\n"

    pred = lab[["id"]].assign(formation_energy_ev_natom=0.5, bandgap_energy_ev=2.0)
    result = ev.score(write(run, pred))
    assert result.error is None and result.test_score == pytest.approx(0.0)
    sub = pd.read_csv(run / "nodes" / "n0" / "submission.csv")
    assert sub["id"].tolist() == list(range(1, 7))  # original test ids, in MLE-bench's order
    assert "must not be negative" in ev.score(write(run, pred.assign(bandgap_energy_ev=-1.0))).error


def test_cactus_unzips_images(data: Path, tmp_path: Path):
    """Train and test images are unzipped into one images/ folder named by id; AUC is scored."""
    run = tmp_path / "run"
    ctx = ev.prepare(CACTUS, run, seed=0)
    assert len(list((ctx.input_dir / "images").iterdir())) == 36
    lab = labels(run)
    result = ev.score(write(run, pd.DataFrame({"id": lab["id"], "has_cactus": lab["label"].astype(float)})))
    assert result.error is None and result.val_score == 1.0 and result.test_score == 1.0
    assert ctx.higher_is_better


def test_controller_runs_on_the_stand_in(data: Path, tmp_path: Path):
    """A real script in a subprocess, scored by the stand-in: the node works, and the test score is stored."""
    script = (
        "import os\nimport pandas as pd\n"
        "p = pd.read_csv('input/predict.csv')\n"
        "for a in ['EAP', 'HPL', 'MWS']:\n    p[a] = 1 / 3\n"
        "p[['id', 'EAP', 'HPL', 'MWS']].to_csv(os.path.join(OUTPUT_DIR, 'predictions.csv'), index=False)\n"
    )

    def llm(*, agent: str, system: str, user: str) -> str:
        """Always the same uniform-probability script."""
        return f"PLAN: uniform.\n\n```python\n{script}```\n"

    cfg = load_config(REPO / "configs" / "conditions" / "c1_autonomous.yaml")
    cfg["budget"].update({"max_nodes": 1})
    cfg["agents"].update({"retrieval": False, "reflection": False})
    cfg["evaluator"] = "stand_in"
    c = Controller(cfg, SPOOKY, 0, tmp_path / "run", llm=llm, sandbox=SubprocessSandbox(), evaluator=ev)
    node = c.run().nodes["n0"]
    assert node.error is None
    assert node.val_score == pytest.approx(np.log(3)) and node.test_score == pytest.approx(np.log(3))
    assert (tmp_path / "run" / "submission.csv").exists()
    assert json.loads((tmp_path / "run" / "task_context.json").read_text())["metric"] == "multi-class log loss"


def test_unknown_task_and_missing_data(tmp_path: Path, monkeypatch):
    """A task outside the six, or data that was never prepared, fails with a clear message."""
    monkeypatch.setenv("MLEBENCH_DATA_DIR", str(tmp_path / "empty"))
    with pytest.raises(ValueError, match="no stand-in evaluator"):
        ev.prepare("titanic", tmp_path / "run", seed=0)
    with pytest.raises(FileNotFoundError, match="mlebench prepare -c"):
        ev.prepare(SPOOKY, tmp_path / "run", seed=0)


def test_target_column_is_named_as_the_task_note_says():
    """Each classification task's train.csv keeps its original target name, which the note given to A3 uses."""
    for name, task in ev.TASKS.items():
        if task.kind == "regression":
            assert task.label_name == "", name  # regression targets keep their own names already
        else:
            assert task.label_name and task.label_name in task.files_note, name
