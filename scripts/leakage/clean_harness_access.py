"""Clean control for R0: reads ./input only, and prints text that merely mentions paths."""

import os

import numpy as np
import pandas as pd

OUTPUT_DIR = "output"
FEATURES = ["f1", "f2", "f3", "f4"]


class Logistic:
    """Logistic regression by gradient descent, numpy only."""

    def fit(self, X, y, steps=300, lr=0.1):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        self.mu, self.sd = np.mean(X, axis=0), np.std(X, axis=0) + 1e-9
        Z = (X - self.mu) / self.sd
        self.w, self.b = np.zeros(Z.shape[1]), 0.0
        for _ in range(steps):
            p = 1 / (1 + np.exp(-(Z @ self.w + self.b)))
            self.w = self.w - lr * Z.T @ (p - y) / len(y)
            self.b = self.b - lr * float(np.mean(p - y))
        return self

    def predict_proba(self, X):
        Z = (np.asarray(X, dtype=float) - self.mu) / self.sd
        p = 1 / (1 + np.exp(-(Z @ self.w + self.b)))
        return np.column_stack([1 - p, p])


def train_test_split(X, y, test_size=0.2, random_state=0):
    """Hold out a random share of rows; scikit-learn's argument and return order."""
    idx = np.random.default_rng(random_state).permutation(len(X))
    cut = int(len(X) * (1 - test_size))
    return X.iloc[idx[:cut]], X.iloc[idx[cut:]], y.iloc[idx[:cut]], y.iloc[idx[cut:]]


def log_loss(y, p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


train = pd.read_csv(os.path.join("input", "train.csv"))
test = pd.read_csv(os.path.join("input", "predict.csv"))
y = train["outcome"]

print("Loading... input/train.csv has", len(train), "rows")
X = train[FEATURES].fillna(0)
model = Logistic()
model.fit(X, y)
proba = model.predict_proba(test[FEATURES].fillna(0))[:, 1]

os.makedirs(OUTPUT_DIR, exist_ok=True)
pd.DataFrame({"id": test["id"], "outcome": proba}).to_csv(os.path.join(OUTPUT_DIR, "predictions.csv"), index=False)
