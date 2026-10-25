"""A small seeded dataset for the planted-leakage scripts, in the layout A3's scripts see.

    <workspace>/input/train.csv     id, f1..f4, outcome (0 or 1); f2 has missing values
    <workspace>/input/predict.csv   id, f1..f4 for the held-out rows, unlabelled

The rows are split with imle.splits.carve (validation and probe rows go to predict.csv,
as in a real run). No competition data is involved.

    python scripts/leakage/make_data.py <workspace> [--seed 0] [--rows 400]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from imle.splits import carve

TARGET = "outcome"


def make(workspace: Path, seed: int = 0, rows: int = 400) -> Path:
    """Write train.csv and predict.csv under workspace/input; return the input folder."""
    rng = np.random.default_rng(seed)
    features = rng.normal(size=(rows, 4))
    logits = 1.5 * features[:, 0] - 0.8 * features[:, 1]
    outcome = (rng.random(rows) < 1 / (1 + np.exp(-logits))).astype(int)
    df = pd.DataFrame(features.round(4), columns=["f1", "f2", "f3", "f4"])
    df.insert(0, "id", [f"r{i:04d}" for i in range(rows)])
    df.loc[rng.random(rows) < 0.1, "f2"] = np.nan
    df[TARGET] = outcome
    split = carve(df, val_fraction=0.2, probe_fraction=0.1, seed=seed, label=TARGET)
    inputs = workspace / "input"
    inputs.mkdir(parents=True, exist_ok=True)
    df[split == "train"].to_csv(inputs / "train.csv", index=False)
    df[split != "train"].drop(columns=[TARGET]).to_csv(inputs / "predict.csv", index=False)
    return inputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rows", type=int, default=400)
    args = parser.parse_args()
    print(make(args.workspace, args.seed, args.rows))
