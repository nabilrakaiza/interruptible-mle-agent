"""Seeded train / validation / probe carve-out, numpy only.

Live runs use the stand-in evaluator's split (imle.stand_in_evaluation), so every
condition sees the same rows as the C1 runs. This module builds the same kind of
split for synthetic data: the leakage scripts and the tests.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SPLITS = ("train", "val", "probe")


def carve(df: pd.DataFrame, val_fraction: float = 0.2, probe_fraction: float = 0.1, seed: int = 0,
          label: str | None = None) -> pd.Series:
    """Assign each row of `df` to train, val or probe; stratified by `label` when given.

    Deterministic for a given seed and row order. Each class (or the whole frame) gets
    round(fraction * size) validation and probe rows, so small classes may get none.
    """
    if val_fraction < 0 or probe_fraction < 0 or val_fraction + probe_fraction >= 1:
        raise ValueError("fractions must be non-negative and sum to less than 1")
    rng = np.random.default_rng(seed)
    out = pd.Series("train", index=df.index, dtype=object)
    groups = [df.index] if label is None else [
        df.index[(df[label] == value).to_numpy()] for value in sorted(df[label].unique(), key=str)
    ]
    for index in groups:
        order = index[rng.permutation(len(index))]
        n_val, n_probe = round(val_fraction * len(index)), round(probe_fraction * len(index))
        out[order[:n_val]] = "val"
        out[order[n_val:n_val + n_probe]] = "probe"
    return out


def check_disjoint(split: pd.Series, ids: pd.Series) -> None:
    """Raise ValueError if any ID appears in more than one split."""
    seen = pd.DataFrame({"id": ids.to_numpy(), "split": split.to_numpy()}).drop_duplicates()
    shared = seen[seen["id"].duplicated(keep=False)]
    if not shared.empty:
        raise ValueError(f"ids in more than one split: {sorted(map(str, shared['id'].unique()))[:5]}")
