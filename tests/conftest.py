"""Shared fixtures for role 3's tests: a tiny MLE-bench-style spooky dataset."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SPOOKY = "spooky-author-identification"
AUTHORS = ["EAP", "HPL", "MWS"]


def write_spooky(root: Path, n_train: int = 60, n_test: int = 9) -> None:
    """MLE-bench's prepared layout for spooky: public train/test/description, private test answers."""
    pub, priv = root / SPOOKY / "prepared" / "public", root / SPOOKY / "prepared" / "private"
    pub.mkdir(parents=True)
    priv.mkdir(parents=True)
    authors = [AUTHORS[i % 3] for i in range(n_train)]
    pd.DataFrame({"id": [f"id{i:03}" for i in range(n_train)], "text": [f"text {a} {i}" for i, a in enumerate(authors)],
                  "author": authors}).to_csv(pub / "train.csv", index=False)
    pd.DataFrame({"id": [f"t{i}" for i in range(n_test)], "text": "x"}).to_csv(pub / "test.csv", index=False)
    answers = pd.DataFrame({"id": [f"t{i}" for i in range(n_test)]})
    for j, a in enumerate(AUTHORS):
        answers[a] = [int(i % 3 == j) for i in range(n_test)]
    answers.to_csv(priv / "test.csv", index=False)
    (pub / "description.md").write_text("# Overview\n\nGuess the author.")


@pytest.fixture
def spooky_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """MLEBENCH_DATA_DIR pointing at a tiny spooky dataset; needs scikit-learn for the stand-in's split."""
    pytest.importorskip("sklearn")
    root = tmp_path / "mlebench"
    write_spooky(root)
    monkeypatch.setenv("MLEBENCH_DATA_DIR", str(root))
    return root


def uniform_predictions(input_dir: Path, rng_seed: int | None = None) -> pd.DataFrame:
    """Predictions for every row of predict.csv: uniform, or random Dirichlet rows when a seed is given."""
    ids = pd.read_csv(input_dir / "predict.csv")["id"]
    if rng_seed is None:
        probs = np.full((len(ids), 3), 1 / 3)
    else:
        probs = np.random.default_rng(rng_seed).dirichlet(np.ones(3), size=len(ids))
    return pd.DataFrame({"id": ids, **{a: probs[:, i] for i, a in enumerate(AUTHORS)}})
