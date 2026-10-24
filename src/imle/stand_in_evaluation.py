"""Stand-in A1 for the six MLE-bench tasks, until role 3's `agents/evaluation.py` exists.

Temporary, written by role 2 so real runs can start. It has the same `prepare` and
`score` functions the controller expects from A1 (docs/core-agent-assumptions.md), and
no leakage screen. Choose it with `python -m imle.controller --evaluator stand_in`.

It reads the data MLE-bench prepared (`mlebench prepare -c <task>`) from
$MLEBENCH_DATA_DIR, by default MLE-bench's cache folder, and for each run writes:

    <run_dir>/stand_in/input/      what the agent sees (hard-linked into workspace/input)
        train.csv                  the train split, labelled
        predict.csv                validation, probe and test rows, shuffled, unlabelled
        images/ or geometry/       the task's other files, named by the ids in the CSVs
    <run_dir>/stand_in/harness/    never shown to the agent
        labels.csv                 id, split (val / probe / test), the truth, and for
                                   test rows their position and id in MLE-bench's test set
        meta.json                  task, kind, targets, classes

Splits: MLE-bench's public train set is split into train, validation (`splits.val_fraction`,
default 0.2) and probe (`splits.probe_fraction`, 0.1), stratified for classification. The
split uses `splits.seed` (default 0), not the run seed, so every condition and seed of a
task sees the same split. The test rows are MLE-bench's test set, graded against its
private answers.

Scores use the same metric code as MLE-bench's grade.py for each task, and predictions
that MLE-bench would reject (wrong ids, probabilities that do not sum to one, ...) are
rejected here too. `score` also returns `test_score`, which the controller stores on the
node for analysis only, and writes the test rows to submission.csv in MLE-bench's format,
so `mlebench grade-sample` can re-grade it.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import yaml

ROOT_DIR = "stand_in"


def data_dir() -> Path:
    """Where MLE-bench keeps prepared data: $MLEBENCH_DATA_DIR, else its default cache folder."""
    if os.environ.get("MLEBENCH_DATA_DIR"):
        return Path(os.environ["MLEBENCH_DATA_DIR"]).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "mle-bench" / "data"
    return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "mle-bench" / "data"


@dataclass
class Task:
    """How one MLE-bench task maps onto train.csv / predict.csv / predictions.csv."""

    kind: str                  # multiclass | binary | regression
    targets: list[str]         # prediction columns besides id (multiclass: one per class)
    metric: str
    higher_is_better: bool
    prediction_format: str
    files_note: str            # appended to the competition description
    label_name: str = ""       # the target's column name in the agent's train.csv, as in the original data


TASKS = {
    "spooky-author-identification": Task(
        kind="multiclass", targets=["EAP", "HPL", "MWS"], metric="multi-class log loss", higher_is_better=False,
        prediction_format="Columns id,EAP,HPL,MWS: one row per row of predict.csv, with the predicted probability "
                          "of each author. Each row's probabilities must sum to 1.",
        files_note="train.csv has columns id, text and author (EAP, HPL or MWS). predict.csv has id and text.",
        label_name="author",
    ),
    "detecting-insults-in-social-commentary": Task(
        kind="binary", targets=["Insult"], metric="AUC", higher_is_better=True,
        prediction_format="Columns id,Insult: one row per row of predict.csv, where Insult is the predicted "
                          "probability (between 0 and 1) that the comment is insulting.",
        files_note="train.csv has columns id, Date, Comment and Insult (1 if insulting). predict.csv has id, "
                   "Date and Comment. Date is often empty.",
        label_name="Insult",
    ),
    "random-acts-of-pizza": Task(
        kind="binary", targets=["requester_received_pizza"], metric="AUC", higher_is_better=True,
        prediction_format="Columns id,requester_received_pizza: one row per row of predict.csv, where "
                          "requester_received_pizza is the predicted probability (between 0 and 1) of success.",
        files_note="The JSON records are given as CSV: train.csv and predict.csv have one row per request, with "
                   "id (the request_id) and the fields known at request time; requester_subreddits_at_request is "
                   "a JSON list. Fields only known later (the *_at_retrieval fields, requester_user_flair, "
                   "post_was_edited, request_text) are removed, because the test set does not have them. "
                   "train.csv also has requester_received_pizza (1 or 0).",
        label_name="requester_received_pizza",
    ),
    "nomad2018-predict-transparent-conductors": Task(
        kind="regression", targets=["formation_energy_ev_natom", "bandgap_energy_ev"],
        metric="mean RMSLE of the two targets", higher_is_better=False,
        prediction_format="Columns id,formation_energy_ev_natom,bandgap_energy_ev: one row per row of predict.csv. "
                          "Predictions must not be negative.",
        files_note="train.csv and predict.csv have the material's columns, and train.csv also has "
                   "formation_energy_ev_natom and bandgap_energy_ev. The ids are renumbered for this run; the atom "
                   "positions for a row are in geometry/<id>.xyz.",
    ),
    "aerial-cactus-identification": Task(
        kind="binary", targets=["has_cactus"], metric="AUC", higher_is_better=True,
        prediction_format="Columns id,has_cactus: one row per row of predict.csv, where has_cactus is the predicted "
                          "probability (between 0 and 1) that the image contains a cactus.",
        files_note="train.csv has columns id and has_cactus; predict.csv has id. Each id is an image file name "
                   "in images/ (32x32 colour JPEGs).",
        label_name="has_cactus",
    ),
    "leaf-classification": Task(
        kind="multiclass", targets=[], metric="multi-class log loss", higher_is_better=False,
        prediction_format="Columns id and one column per species, named and ordered as in the list of species "
                          "below: one row per row of predict.csv, with the predicted probability of each species. "
                          "Each row's probabilities must sum to 1.",
        files_note="train.csv has id, species and the 192 precomputed features (margin, shape, texture); "
                   "predict.csv has id and the features. images/<id>.jpg is the leaf's binary image.",
        label_name="species",
    ),
}


# --------------------------------------------------------------------------- loading


def _load(task: str, public: Path, private: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """(train, test, test truth, classes) in a common shape.

    train has id, the features and a `label` column (class name, 0/1, or the regression
    targets under their own names). test has `orig_id` (MLE-bench's key for the row), id
    and the features, in MLE-bench's test order. truth has the test rows' labels in the
    same order.
    """
    spec = TASKS[task]
    if task == "spooky-author-identification":
        train = pd.read_csv(public / "train.csv").rename(columns={"author": "label"})
        test = pd.read_csv(public / "test.csv")
        answers = pd.read_csv(private / "test.csv").set_index("id").loc[test["id"]]
        truth = pd.DataFrame({"label": answers[spec.targets].idxmax(axis=1).to_numpy()})
        test.insert(0, "orig_id", test["id"])
        return train, test, truth, spec.targets

    if task == "leaf-classification":
        classes = list(pd.read_csv(public / "sample_submission.csv", nrows=0).columns[1:])
        train = pd.read_csv(public / "train.csv").rename(columns={"species": "label"})
        test = pd.read_csv(public / "test.csv")
        answers = pd.read_csv(private / "test.csv").set_index("id").loc[test["id"]]
        truth = pd.DataFrame({"label": answers[classes].idxmax(axis=1).to_numpy()})
        test.insert(0, "orig_id", test["id"])
        return train, test, truth, classes

    if task == "detecting-insults-in-social-commentary":
        train = pd.read_csv(public / "train.csv").rename(columns={"Insult": "label"})
        train.insert(0, "id", [f"c{i}" for i in range(len(train))])
        test = pd.read_csv(public / "test.csv")
        answers = pd.read_csv(private / "test.csv")
        if not answers["Comment"].equals(test["Comment"]):
            raise ValueError("private test.csv is not in the order of public test.csv")
        test.insert(0, "id", [f"t{i}" for i in range(len(test))])
        test.insert(0, "orig_id", test["Comment"])
        return train[["id", "Date", "Comment", "label"]], test, pd.DataFrame({"label": answers["Insult"]}), []

    if task == "random-acts-of-pizza":
        test_records = json.loads((public / "test.json").read_text(encoding="utf-8"))
        keep = list(test_records[0])
        target = "requester_received_pizza"

        def table(records: list[dict], label: bool) -> pd.DataFrame:
            """Records as rows, lists as JSON text, request_id renamed to id."""
            df = pd.DataFrame([{k: r.get(k) for k in keep + ([target] if label else [])} for r in records])
            df["requester_subreddits_at_request"] = df["requester_subreddits_at_request"].map(json.dumps)
            return df.rename(columns={"request_id": "id", target: "label"})

        train = table(json.loads((public / "train.json").read_text(encoding="utf-8")), label=True)
        train["label"] = train["label"].astype(int)
        test = table(test_records, label=False)
        answers = pd.read_csv(private / "test.csv").set_index("request_id").loc[test["id"]]
        test.insert(0, "orig_id", test["id"])
        return train, test, pd.DataFrame({"label": answers[target].astype(int).to_numpy()}), []

    if task == "nomad2018-predict-transparent-conductors":
        train = pd.read_csv(public / "train.csv")
        test = pd.read_csv(public / "test.csv")
        answers = pd.read_csv(private / "test.csv").set_index("id").loc[test["id"]]
        test.insert(0, "orig_id", test["id"])
        return train, test, answers[spec.targets].reset_index(drop=True), []

    if task == "aerial-cactus-identification":
        train = pd.read_csv(public / "train.csv").rename(columns={"has_cactus": "label"})
        test = pd.read_csv(public / "sample_submission.csv")[["id"]]
        answers = pd.read_csv(private / "test.csv").set_index("id").loc[test["id"]]
        test.insert(0, "orig_id", test["id"])
        return train, test, pd.DataFrame({"label": answers["has_cactus"].to_numpy()}), []

    raise ValueError(f"no stand-in evaluator for task {task!r}; known: {', '.join(TASKS)}")


def _split(train: pd.DataFrame, kind: str, val_fraction: float, probe_fraction: float, seed: int) -> pd.Series:
    """train / val / probe for each row of MLE-bench's train set, stratified for classification when possible."""
    from sklearn.model_selection import train_test_split

    def cut(index: pd.Index, labels: pd.Series | None, size: int) -> tuple[pd.Index, pd.Index]:
        """Split `index` into (rest, part of `size` rows), stratified if every class allows it."""
        try:
            rest, part = train_test_split(index, test_size=size, random_state=seed, stratify=labels)
        except ValueError:  # a class with too few rows for this part
            rest, part = train_test_split(index, test_size=size, random_state=seed)
        return pd.Index(rest), pd.Index(part)

    stratify = kind != "regression"
    n = len(train)
    split = pd.Series("train", index=train.index)
    rest, val = cut(train.index, train["label"] if stratify else None, round(val_fraction * n))
    _, probe = cut(rest, train.loc[rest, "label"] if stratify else None, round(probe_fraction * n))
    split[val], split[probe] = "val", "probe"
    return split


def _link(src: Path, dst: Path) -> None:
    """Hard-link a file, or copy it across filesystems."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _aux_files(task: str, public: Path, inputs: Path, new_ids: dict[tuple[str, object], object]) -> None:
    """The task's non-CSV files, named by the ids the agent sees."""
    if task == "leaf-classification":
        for image in (public / "images").iterdir():
            _link(image, inputs / "images" / image.name)
    elif task == "aerial-cactus-identification":
        for name in ("train.zip", "test.zip"):
            with zipfile.ZipFile(public / name) as z:
                for member in z.infolist():
                    if not member.is_dir() and member.filename.lower().endswith(".jpg"):
                        target = inputs / "images" / Path(member.filename).name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(z.read(member))
    elif task == "nomad2018-predict-transparent-conductors":
        for (source, old), new in new_ids.items():
            _link(public / source / str(old) / "geometry.xyz", inputs / "geometry" / f"{new}.xyz")


# --------------------------------------------------------------------------- A1 interface


def prepare(task: str, run_dir: Path, seed: int) -> SimpleNamespace:
    """Build the splits and input files for `task` under run_dir/stand_in. Returns the task context."""
    spec = TASKS.get(task)
    if spec is None:
        raise ValueError(f"no stand-in evaluator for task {task!r}; known: {', '.join(TASKS)}")
    prepared = data_dir() / task / "prepared"
    public, private = prepared / "public", prepared / "private"
    if not (public.exists() and private.exists()):
        raise FileNotFoundError(f"{prepared} not found: run `mlebench prepare -c {task}`, or set MLEBENCH_DATA_DIR")

    cfg_path = run_dir / "config.yaml"
    cfg = (yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}) if cfg_path.exists() else {}
    splits = cfg.get("splits") or {}
    split_seed = splits.get("seed", 0)

    train, test, truth, classes = _load(task, public, private)
    train = train.reset_index(drop=True)
    train["split"] = _split(train, spec.kind, splits.get("val_fraction", 0.2), splits.get("probe_fraction", 0.1),
                            split_seed)
    targets = spec.targets or classes
    label_cols = spec.targets if spec.kind == "regression" else ["label"]

    new_ids: dict[tuple[str, object], object] = {}
    if task == "nomad2018-predict-transparent-conductors":
        # Train and test ids overlap in the original; renumber every row, in shuffled order.
        order = np.random.default_rng(split_seed).permutation(len(train) + len(test)) + 1
        new_ids = {("train", old): int(new) for old, new in zip(train["id"], order[: len(train)])}
        new_ids.update({("test", old): int(new) for old, new in zip(test["id"], order[len(train):])})
        train["id"] = [new_ids[("train", old)] for old in train["id"]]
        test["id"] = [new_ids[("test", old)] for old in test["id"]]

    root = run_dir / ROOT_DIR
    inputs, harness = root / "input", root / "harness"
    if root.exists():
        shutil.rmtree(root)  # a run that crashed inside prepare starts over
    inputs.mkdir(parents=True)
    harness.mkdir(parents=True)

    features = [c for c in train.columns if c not in label_cols and c != "split"]
    # Internally the target is `label`; the agent sees it under its original name, as the description says.
    train_out = train[train.split == "train"][features + label_cols]
    train_out.rename(columns={"label": spec.label_name} if spec.label_name else {}).to_csv(
        inputs / "train.csv", index=False)
    holdout = train[train.split != "train"]
    test = test.copy().assign(split="test", position=range(len(test)))  # copy: de-fragment after inserts
    predict = pd.concat([holdout[features], test[features]], ignore_index=True)
    predict.sample(frac=1, random_state=split_seed).to_csv(inputs / "predict.csv", index=False)

    test_labels = pd.concat([test[["id", "split", "position", "orig_id"]].reset_index(drop=True), truth], axis=1)
    holdout_labels = holdout[["id", "split", *label_cols]].assign(position=-1, orig_id="")
    pd.concat([holdout_labels, test_labels], ignore_index=True).to_csv(harness / "labels.csv", index=False)
    if task == "detecting-insults-in-social-commentary":
        test[["id", "Date", "Comment"]].to_csv(harness / "test_rows.csv", index=False)
    meta = {"task": task, "kind": spec.kind, "targets": targets, "label_cols": label_cols,
            "id_dtype": str(train["id"].dtype), "split_seed": split_seed,
            "rows": {s: int((train.split == s).sum()) for s in ("train", "val", "probe")} | {"test": len(test)}}
    (harness / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _aux_files(task, public, inputs, new_ids)

    description = (public / "description.md").read_text(encoding="utf-8").strip()
    files = spec.files_note + (f"\n\nSpecies, in the order of the prediction columns: {', '.join(classes)}."
                               if task == "leaf-classification" else "")
    description += (
        "\n\n# Files for this run\n\nThe file names and submission format above are from the original "
        "competition. In this run the data is laid out as follows, and predictions go to predictions.csv "
        f"as described under Output.\n\n{files}"
    )
    return SimpleNamespace(description=description, input_dir=inputs, prediction_format=spec.prediction_format,
                           metric=spec.metric, higher_is_better=spec.higher_is_better)


def _result(val=None, probe=None, test=None, error: str | None = None) -> SimpleNamespace:
    """A ScoreResult, with test_score for analysis."""
    return SimpleNamespace(val_score=val, probe_score=probe, test_score=test, error=error)


def _check(pred: pd.DataFrame, labels: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """The predictions joined to the labels, or ValueError saying what MLE-bench would reject."""
    targets = meta["targets"]
    missing = [c for c in ["id", *targets] if c not in pred.columns]
    if missing:
        raise ValueError(f"missing columns {missing}; expected id,{','.join(targets)}")
    pred = pred[["id", *targets]].copy()
    if meta["id_dtype"].startswith("int"):
        ids = pd.to_numeric(pred["id"], errors="coerce")
        if ids.isna().any() or (ids != ids.round()).any():
            raise ValueError("ids must be the integers in predict.csv")
        pred["id"] = ids.astype("int64")
    else:
        pred["id"] = pred["id"].astype(str)
    if pred["id"].duplicated().any():
        raise ValueError("duplicate ids")
    if set(pred["id"]) != set(labels["id"]) or len(pred) != len(labels):
        raise ValueError(f"ids do not match predict.csv: {len(pred)} rows, expected {len(labels)}")
    values = pred[targets].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any():
        raise ValueError("predictions must be numbers, with no missing values")
    if meta["kind"] in ("binary", "multiclass") and ((values < 0) | (values > 1)).any().any():
        raise ValueError("probabilities must be between 0 and 1")
    if meta["kind"] == "multiclass" and not np.allclose(values.sum(axis=1), 1, atol=1e-6):
        raise ValueError("each row's probabilities must sum to 1")
    if meta["kind"] == "regression" and (values < 0).any().any():
        raise ValueError("predictions must not be negative")
    pred[targets] = values
    return labels.merge(pred, on="id", how="left")


def metric(part: pd.DataFrame, meta: dict) -> float:
    """The task's metric on some rows, computed as MLE-bench's grade.py computes it."""
    from sklearn.metrics import log_loss, roc_auc_score, root_mean_squared_log_error

    targets = meta["targets"]
    if meta["kind"] == "multiclass":
        y_true = (part["label"].to_numpy()[:, None] == np.array(targets)[None, :]).astype(int)
        return float(log_loss(y_true, part[targets].to_numpy()))
    if meta["kind"] == "binary":
        return float(roc_auc_score(part["label"].astype(int), part[targets[0]]))
    return float(np.mean([root_mean_squared_log_error(part[f"{t}_x"], part[f"{t}_y"]) for t in targets]))


def _submission(joined: pd.DataFrame, meta: dict, harness: Path) -> pd.DataFrame:
    """The test rows in MLE-bench's submission format and row order."""
    test = joined[joined.split == "test"].sort_values("position")
    targets = meta["targets"]
    if meta["task"] == "detecting-insults-in-social-commentary":
        rows = pd.read_csv(harness / "test_rows.csv").set_index("id").loc[test["id"]]
        return pd.DataFrame({"Insult": test["Insult"].to_numpy(), "Date": rows["Date"].to_numpy(),
                             "Comment": rows["Comment"].to_numpy()})
    key = "request_id" if meta["task"] == "random-acts-of-pizza" else "id"
    cols = {t: test[f"{t}_y" if meta["kind"] == "regression" else t].to_numpy() for t in targets}
    orig = test["orig_id"].to_numpy()
    if meta["id_dtype"].startswith("int"):
        orig = orig.astype(float).astype(int)
    return pd.DataFrame({key: orig, **cols})


def labelled_predictions(node_dir: Path) -> tuple[pd.DataFrame, dict]:
    """A node's predictions joined to the labels, and the task's meta.

    One row per held-out row, in labels.csv order, so two nodes' frames line up row by row.
    Raises ValueError (or a pandas parsing error) for predictions MLE-bench would reject.
    """
    harness = node_dir.parent.parent / ROOT_DIR / "harness"
    meta = json.loads((harness / "meta.json").read_text(encoding="utf-8"))
    labels = pd.read_csv(harness / "labels.csv", dtype={"id": str} if not meta["id_dtype"].startswith("int") else None,
                         keep_default_na=False, na_values=[""])
    return _check(pd.read_csv(node_dir / "output" / "predictions.csv"), labels, meta), meta


def paired_worse_share(run_dir: Path, node_id: str, other_id: str, split: str, higher_is_better: bool,
                       samples: int = 1000) -> float | None:
    """Share of paired bootstrap resamples of the `split` rows on which `node_id` scores worse than `other_id`.

    Both nodes are scored on the same resampled rows each time, so what is left is the noise
    in their difference. None when the run has no stand-in labels (role 3's A1 keeps them
    elsewhere) or a node's predictions cannot be scored. Seeded, so the same inputs always
    give the same share.
    """
    if not (run_dir / ROOT_DIR / "harness" / "labels.csv").exists():
        return None
    try:
        (mine, meta), (theirs, _) = (labelled_predictions(run_dir / "nodes" / n) for n in (node_id, other_id))
    except (ValueError, OSError, pd.errors.ParserError, pd.errors.EmptyDataError):
        return None
    rows = np.flatnonzero((mine["split"] == split).to_numpy())
    rng = np.random.default_rng(0)
    results = []
    for _ in range(samples):
        pick = rng.choice(rows, len(rows))
        try:
            a, b = metric(mine.iloc[pick], meta), metric(theirs.iloc[pick], meta)
        except ValueError:  # e.g. AUC on a resample with one class
            continue
        results.append(a < b if higher_is_better else a > b)
    return float(np.mean(results)) if results else None


def score(node_dir: Path) -> SimpleNamespace:
    """Validation, probe and test scores of node_dir/output/predictions.csv; writes node_dir/submission.csv.

    Missing or malformed predictions come back as `error`, never as an exception.
    """
    harness = node_dir.parent.parent / ROOT_DIR / "harness"
    if not (node_dir / "output" / "predictions.csv").exists():
        return _result(error="predictions.csv not found")
    try:
        joined, meta = labelled_predictions(node_dir)
        scores = {s: metric(joined[joined.split == s], meta) for s in ("val", "probe", "test")}
    except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as e:
        return _result(error=str(e)[:500])
    _submission(joined, meta, harness).to_csv(node_dir / "submission.csv", index=False)
    return _result(scores["val"], scores["probe"], scores["test"])
