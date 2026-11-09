"""Run one node script unchanged and capture the feature matrices it feeds to its linear classifiers.

Usage: python capture.py <solution.py> <input_dir> <out_dir>

Patches fit / predict_proba / decision_function of LogisticRegression, SGDClassifier and LinearSVC.
A fit on all training rows records (X, y) for that estimator; a later prediction on all predict
rows records X_pred and the estimator's own scores. CV fits on fewer rows are ignored. The
script's own predictions.csv is kept, to check the run reproduces the node.
"""
import os, sys, shutil, runpy, pickle
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.svm import LinearSVC

script, input_dir, out_dir = (os.path.abspath(a) for a in sys.argv[1:4])
os.makedirs(out_dir, exist_ok=True)
n_train = len(pd.read_csv(os.path.join(input_dir, "train.csv")))
n_pred = len(pd.read_csv(os.path.join(input_dir, "predict.csv")))
captured = {}  # id(estimator) -> dict


def as_csr(X):
    """A copy of X as float64 CSR, whatever it came in as."""
    return sparse.csr_matrix(X, dtype=np.float64) if not sparse.issparse(X) else X.tocsr().astype(np.float64)


def patch(cls):
    """Wrap fit and the scoring methods of `cls` to record full-size calls."""
    fit0 = cls.fit
    def fit(self, X, y, *a, **k):
        out = fit0(self, X, y, *a, **k)
        if X.shape[0] == n_train:
            captured[id(self)] = {"cls": cls.__name__, "params": self.get_params(), "X": as_csr(X), "y": np.asarray(y)}
        return out
    cls.fit = fit
    for name in ("predict_proba", "decision_function"):
        if not hasattr(cls, name):
            continue
        f0 = getattr(cls, name)
        def wrapped(self, X, *a, _f0=f0, _name=name, **k):
            out = _f0(self, X, *a, **k)
            c = captured.get(id(self))
            if c is not None and X.shape[0] == n_pred and "X_pred" not in c:
                c["X_pred"] = as_csr(X)
                s = np.asarray(out)
                c["own_score"] = s[:, 1] if s.ndim == 2 else s
            return out
        setattr(cls, name, wrapped)


for cls in (LogisticRegression, SGDClassifier, LinearSVC):
    patch(cls)

work = os.path.join(out_dir, "work")
shutil.rmtree(work, ignore_errors=True)
os.makedirs(os.path.join(work, "out"))
os.symlink(os.path.abspath(input_dir), os.path.join(work, "input"))
os.environ["OUTPUT_DIR"] = os.path.join(work, "out")
os.chdir(work)
runpy.run_path(os.path.abspath(script), init_globals={"OUTPUT_DIR": os.environ["OUTPUT_DIR"]}, run_name="__main__")

done = [c for c in captured.values() if "X_pred" in c]
pickle.dump(done, open(os.path.join(out_dir, "captured.pkl"), "wb"))
shutil.copy(os.path.join(work, "out", "predictions.csv"), os.path.join(out_dir, "predictions.csv"))
print(f"captured {len(done)} full-size classifier(s):", [(c["cls"], c["X"].shape) for c in done])
