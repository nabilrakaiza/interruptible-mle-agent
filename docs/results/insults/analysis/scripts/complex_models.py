"""Fit more complex models on each node's captured features; score validation, probe and test AUC.

Usage: python complex_models.py <cap_dir> <selection.json> <runs_root> <out.csv>

For each node: (1) the node as originally scored, (2) the rerun's own predictions.csv (checks the
rerun reproduces the node), (3) its captured logistic regression on its own, and (4) LightGBM,
XGBoost, random forest and extra trees on the same captured matrix. Settings are fixed in advance;
nothing is tuned on validation, probe or test. A node with several full-size linear classifiers
(a blend) gets its matrices stacked side by side, minus any small meta-level matrix.
"""
import json, os, pickle, sys, time
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
import lightgbm as lgb
import xgboost as xgb

cap_dir, sel_path, runs_root, out_csv = sys.argv[1:5]
sel = json.load(open(sel_path))
TASK = "detecting-insults-in-social-commentary"

MODELS = {
    "LightGBM": lambda: lgb.LGBMClassifier(n_estimators=600, learning_rate=0.05, num_leaves=31, min_child_samples=10,
                                           colsample_bytree=0.3, subsample=0.8, subsample_freq=1, reg_lambda=1.0,
                                           random_state=0, n_jobs=2, verbose=-1),
    "XGBoost": lambda: xgb.XGBClassifier(n_estimators=600, learning_rate=0.05, max_depth=6, colsample_bytree=0.3,
                                         subsample=0.8, tree_method="hist", random_state=0, n_jobs=2),
    "RandomForest": lambda: RandomForestClassifier(n_estimators=500, max_features="sqrt", min_samples_leaf=1,
                                                   random_state=0, n_jobs=2),
    "ExtraTrees": lambda: ExtraTreesClassifier(n_estimators=500, max_features="sqrt", min_samples_leaf=1,
                                               random_state=0, n_jobs=2),
}


def scores(pred_ids, p, labels):
    """AUC on validation, probe and test for predictions `p` aligned with `pred_ids`."""
    df = pd.DataFrame({"id": pred_ids, "p": p}).merge(labels, on="id")
    return {sp: roc_auc_score(df[df.split == sp]["label"].astype(int), df[df.split == sp]["p"]) for sp in ("val", "probe", "test")}


rows = []
for group, nodes in sel.items():
    for n in nodes:
        key = f"{n['run']}_{n['id']}"
        run_dir = os.path.join(runs_root, f"{n['run'].rsplit('_seed', 1)[0]}_{TASK}_seed{n['run'].rsplit('seed', 1)[1]}")
        labels = pd.read_csv(os.path.join(run_dir, "stand_in/harness/labels.csv"))
        pred_ids = pd.read_csv(os.path.join(run_dir, "stand_in/input/predict.csv"))["id"].to_numpy()
        base = {"group": f"top3 {group}", "node": key}
        rows.append({**base, "model": "original node", "val": n["val"], "probe": n["probe"], "test": n["test"]})
        own = pd.read_csv(os.path.join(cap_dir, key, "predictions.csv"))
        rows.append({**base, "model": "rerun (check)", **scores(own["id"].to_numpy(), own.iloc[:, 1].to_numpy(), labels)})
        caps = pickle.load(open(os.path.join(cap_dir, key, "captured.pkl"), "rb"))
        big = [c for c in caps if c["X"].shape[1] >= 20] or caps
        if not big:
            rows.append({**base, "model": "no linear classifier captured"}); continue
        X = sparse.hstack([c["X"] for c in big]).tocsr(); Xp = sparse.hstack([c["X_pred"] for c in big]).tocsr()
        y = big[0]["y"].astype(int)
        for i, c in enumerate(big):
            rows.append({**base, "model": f"captured {c['cls']} #{i + 1}", "n_features": c["X"].shape[1],
                         **scores(pred_ids, c["own_score"], labels)})
        for name, make in MODELS.items():
            t = time.time(); m = make(); m.fit(X, y)
            rows.append({**base, "model": name, "n_features": X.shape[1], "fit_s": round(time.time() - t, 1),
                         **scores(pred_ids, m.predict_proba(Xp)[:, 1], labels)})
            print(key, name, {k: round(v, 4) for k, v in rows[-1].items() if k in ("val", "probe", "test")}, flush=True)
pd.DataFrame(rows).to_csv(out_csv, index=False)
print("written", out_csv)
