"""Hand-written metrics and analysis helpers, numpy only.

`multiclass_log_loss` is the spooky-author-identification metric. The live harness
scores with the stand-in's MLE-bench metric code; tests check that the two agree.

`node_table`, `spearman`, `top_k_agreement` and `bootstrap_ci` serve role 3's
analysis scripts (scripts/analyze_*.py). They read runs only through
imle.checkpoint, so they assume no run-folder layout beyond what it defines.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from imle import checkpoint
from imle.tree import NodeStatus, Tree

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


# --------------------------------------------------------------------------- analysis helpers

NODE_COLUMNS = ["run", "condition", "task", "seed", "node_id", "parent_id", "operator", "status", "val_score",
                "probe_score", "test_score", "higher_is_better", "is_final", "is_best_val"]


def node_table(run_dirs: Iterable[Path], condition_key: str = "condition") -> pd.DataFrame:
    """One row per node of each run's latest complete checkpoint.

    Condition, task and seed come from that checkpoint's status.json (`condition_key`
    names the condition field). `is_final` marks the run's submitted node(s)
    (`final_nodes`, else `final_node`); `is_best_val` the best working node by
    validation, which is the final pick under best_val selection.
    """
    rows = []
    for run_dir in sorted(Path(p) for p in run_dirs):
        ck = checkpoint.read(run_dir)
        if ck is None:
            continue
        status, tree = ck["status"], Tree.model_validate(ck["tree"])
        final = set(status.get("final_nodes") or ([status["final_node"]] if status.get("final_node") else []))
        best = tree.best_by_val()
        for node in tree.nodes.values():
            rows.append({"run": run_dir.name, "condition": status.get(condition_key), "task": status.get("task"),
                         "seed": status.get("seed"), "node_id": node.id, "parent_id": node.parent_id,
                         "operator": node.operator.value, "status": node.status.value, "val_score": node.val_score,
                         "probe_score": node.probe_score, "test_score": node.test_score,
                         "higher_is_better": tree.higher_is_better, "is_final": node.id in final,
                         "is_best_val": best is not None and node.id == best.id})
    return pd.DataFrame(rows, columns=NODE_COLUMNS)


def working(nodes: pd.DataFrame, *scores: str) -> pd.DataFrame:
    """Working nodes that have all the given scores."""
    keep = nodes["status"] == NodeStatus.WORKING.value
    for s in scores:
        keep &= nodes[s].notna()
    return nodes[keep]


def spearman(a: Sequence[float], b: Sequence[float]) -> float:
    """Spearman rank correlation (average ranks for ties); NaN with fewer than 3 pairs or a constant input."""
    x, y = pd.Series(a, dtype=float).rank(), pd.Series(b, dtype=float).rank()
    if len(x) < 3 or x.nunique() < 2 or y.nunique() < 2:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def top_k_agreement(a: Sequence[float], b: Sequence[float], k: int, higher_is_better: bool) -> float:
    """Share of the top k items by `a` that are also in the top k by `b` (k capped at the number of items).

    Ties are broken by position, so the result is deterministic.
    """
    n = len(a)
    if n == 0 or k <= 0:
        return float("nan")
    k = min(k, n)
    sign = -1 if higher_is_better else 1
    top_a = set(np.argsort(sign * np.asarray(a, dtype=float), kind="stable")[:k])
    top_b = set(np.argsort(sign * np.asarray(b, dtype=float), kind="stable")[:k])
    return len(top_a & top_b) / k


def bootstrap_ci(values: Sequence[float], level: float = 0.95, n_boot: int = 2000, seed: int = 0
                 ) -> tuple[float, float]:
    """Percentile bootstrap interval for the mean; NaNs are dropped, and an empty input gives (nan, nan)."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return float("nan"), float("nan")
    means = np.random.default_rng(seed).choice(v, size=(n_boot, len(v)), replace=True).mean(axis=1)
    tail = (1 - level) / 2 * 100
    return float(np.percentile(means, tail)), float(np.percentile(means, 100 - tail))


def summarise(table: pd.DataFrame, by: list[str], columns: list[str], seed: int = 0) -> pd.DataFrame:
    """Mean, standard deviation, count and bootstrap 95% CI of each column, per group."""
    rows = []
    for key, group in table.groupby(by, sort=True, dropna=False):
        row = dict(zip(by, key if isinstance(key, tuple) else (key,)))
        for c in columns:
            v = group[c].dropna()
            lo, hi = bootstrap_ci(v.tolist(), seed=seed)
            row.update({f"{c}_mean": v.mean() if len(v) else float("nan"),
                        f"{c}_sd": v.std(ddof=1) if len(v) > 1 else float("nan"),
                        f"{c}_n": len(v), f"{c}_ci_low": lo, f"{c}_ci_high": hi})
        rows.append(row)
    return pd.DataFrame(rows)
