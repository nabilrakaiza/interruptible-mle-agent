"""Hand-written task metrics, numpy only.

`multiclass_log_loss` is the spooky-author-identification metric. The live harness
scores with the stand-in's MLE-bench metric code; tests check that the two agree.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

EPS = 1e-15


def multiclass_log_loss(truth: pd.DataFrame, pred: pd.DataFrame, id_col: str = "id", label_col: str = "label",
                        classes: Sequence[str] = ("EAP", "HPL", "MWS"), eps: float = EPS) -> float:
    """Mean negative log probability of each row's true class.

    `truth` has `id_col` and `label_col` (a class name); `pred` has `id_col` and one
    probability column per class. Rows are matched by ID. Each row is scaled to sum to 1,
    clipped to [eps, 1 - eps] and renormalised; for rows that already sum to 1 this is
    Kaggle's clip-then-normalise.
    """
    classes = list(classes)
    missing = [c for c in [id_col, *classes] if c not in pred.columns]
    if missing:
        raise ValueError(f"missing prediction columns {missing}")
    if pred[id_col].duplicated().any():
        raise ValueError("duplicate ids in predictions")
    joined = truth[[id_col, label_col]].merge(pred[[id_col, *classes]], on=id_col, how="left")
    if len(joined) == 0:
        raise ValueError("no rows to score")
    probs = joined[classes].to_numpy(dtype=float)
    if np.isnan(probs).any():
        raise ValueError("predictions missing for some ids")
    unknown = set(joined[label_col]) - set(classes)
    if unknown:
        raise ValueError(f"labels not among the classes: {sorted(map(str, unknown))}")
    if (probs < 0).any() or (probs.sum(axis=1) <= 0).any():
        raise ValueError("probabilities must be non-negative with a positive row sum")
    # Normalise first so unnormalised scores keep their ratios; then clip and renormalise.
    probs = probs / probs.sum(axis=1, keepdims=True)
    probs = np.clip(probs, eps, 1 - eps)
    probs = probs / probs.sum(axis=1, keepdims=True)
    true_index = joined[label_col].map({c: i for i, c in enumerate(classes)}).to_numpy()
    return float(-np.mean(np.log(probs[np.arange(len(probs)), true_index])))
