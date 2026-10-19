"""Local smoke run: the real agent loop on a toy task, without Kaggle data or Docker.

Uses scikit-learn's bundled breast cancer dataset (no download), a stand-in
evaluator that scores log loss, and the local subprocess sandbox. The run lands
in runs/ like any other, so the dashboard shows it.

    pip install -e ".[sandbox]"
    python scripts/smoke_run.py --provider gemini              # real LLM, a few cents at most
    python scripts/smoke_run.py --dry-run                      # canned replies, no API key needed
    python scripts/smoke_run.py --provider gemini --retrieval web   # A2 reads the allowlisted docs
    python scripts/smoke_run.py --resume runs/smoke_gemini_seed0_...    # continue after a crash

This is a development tool only. The real evaluator for the project tasks is role 3's.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv

from imle.agents.retrieval import WebRetriever
from imle.controller import Controller, latest_complete_checkpoint, load_config
from imle.execution import SubprocessSandbox
from imle.llm import make_llm

ROOT = Path(__file__).resolve().parents[1]
TASK = "toy-breast-cancer"

DESCRIPTION = """\
Predict whether a breast tumour is benign from 30 numeric measurements of cell nuclei
(radius, texture, perimeter, area, smoothness and so on, each as mean, error and worst value).
The column `target` is 1 for benign and 0 for malignant."""

PREDICTION_FORMAT = (
    "Columns id,target: one row per row of predict.csv, where target is the predicted "
    "probability (between 0 and 1) that the tumour is benign."
)

DRY_RUN_SCRIPT = """\
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

train = pd.read_csv("input/train.csv")
predict = pd.read_csv("input/predict.csv")
features = [c for c in train.columns if c not in ("id", "target")]
model = make_pipeline(StandardScaler(), LogisticRegression(C={c}, max_iter=1000))
model.fit(train[features], train["target"])
predict["target"] = model.predict_proba(predict[features])[:, 1]
predict[["id", "target"]].to_csv(os.path.join(OUTPUT_DIR, "predictions.csv"), index=False)
print("done")
"""


class ToyEvaluator:
    """Stand-in A1 for the toy task: fixed splits, log loss on validation and probe."""

    def prepare(self, task: str, run_dir: Path, seed: int) -> SimpleNamespace:
        """Split the dataset 60/15/10/15 into train, validation, probe and test, and save the labels outside the workspace."""
        from sklearn.datasets import load_breast_cancer

        df = load_breast_cancer(as_frame=True).frame
        df.insert(0, "id", np.arange(len(df)))
        order = np.random.default_rng(seed).permutation(len(df))
        cuts = np.cumsum([int(0.60 * len(df)), int(0.15 * len(df)), int(0.10 * len(df))])
        df["split"] = "test"
        for name, idx in zip(("train", "val", "probe"), np.split(order, cuts)[:3]):
            df.loc[idx, "split"] = name

        harness, inputs = run_dir / "toy_harness", run_dir / "toy_input"
        harness.mkdir(parents=True)
        inputs.mkdir(parents=True)
        holdout = df[df.split != "train"]
        holdout[["id", "split", "target"]].to_csv(harness / "labels.csv", index=False)
        df[df.split == "train"].drop(columns="split").to_csv(inputs / "train.csv", index=False)
        holdout.sample(frac=1, random_state=seed).drop(columns=["split", "target"]).to_csv(
            inputs / "predict.csv", index=False
        )
        return SimpleNamespace(
            description=DESCRIPTION,
            input_dir=inputs,
            prediction_format=PREDICTION_FORMAT,
            metric="log loss",
            higher_is_better=False,
        )

    def score(self, node_dir: Path) -> SimpleNamespace:
        """Log loss on validation and probe; writes the test rows to submission.csv. Bad predictions give an error."""
        from sklearn.metrics import log_loss

        labels = pd.read_csv(node_dir.parent.parent / "toy_harness" / "labels.csv")
        path = node_dir / "output" / "predictions.csv"
        if not path.exists():
            return SimpleNamespace(val_score=None, probe_score=None, error="predictions.csv not found")
        try:
            pred = pd.read_csv(path)
            if list(pred.columns) != ["id", "target"]:
                raise ValueError(f"columns are {list(pred.columns)}, expected ['id', 'target']")
            if sorted(pred["id"]) != sorted(labels["id"]):
                raise ValueError("ids do not match predict.csv")
            p = pd.to_numeric(pred["target"])
            if p.isna().any() or (p < 0).any() or (p > 1).any():
                raise ValueError("target must be a probability between 0 and 1")
        except ValueError as e:
            return SimpleNamespace(val_score=None, probe_score=None, error=str(e))

        joined = labels.merge(pred.rename(columns={"target": "pred"}), on="id")
        scores = {
            split: float(log_loss(part["target"], part["pred"].clip(1e-15, 1 - 1e-15), labels=[0, 1]))
            for split, part in joined.groupby("split")
        }
        joined[joined.split == "test"][["id", "pred"]].rename(columns={"pred": "target"}).to_csv(
            node_dir / "submission.csv", index=False
        )
        return SimpleNamespace(val_score=scores["val"], probe_score=scores["probe"], error=None)


class CannedLLM:
    """For --dry-run: replies with a fixed logistic regression script, varying C so improves differ."""

    def __init__(self) -> None:
        """Start the call counter."""
        self.calls = 0

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        """Return the canned plan and script for this call."""
        self.calls += 1
        c = [1.0, 0.1, 10.0, 0.3, 3.0][self.calls % 5]
        return f"PLAN: Scaled logistic regression with C={c}.\n\n```python\n{DRY_RUN_SCRIPT.replace('{c}', str(c))}```\n"


def summarise(run_dir: Path, tree) -> None:
    """Print each node's outcome and the LLM cost of the run."""
    print(f"\nrun folder: {run_dir}")
    for n in tree.nodes.values():
        error = (n.error or "").splitlines()[0][:90] if n.error else ""
        val = f"{n.val_score:.4f}" if n.val_score is not None else "-"
        probe = f"{n.probe_score:.4f}" if n.probe_score is not None else "-"
        print(f"  {n.id:4} {n.operator.value:8} parent={n.parent_id!s:5} {n.status.value:8} "
              f"val={val:7} probe={probe:7} {error}")
    log = run_dir / "llm_calls.jsonl"
    if log.exists():
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        cost = sum(c.get("cost_usd") or 0 for c in calls)
        tokens = sum(c["input_tokens"] + c["output_tokens"] for c in calls)
        print(f"LLM: {len(calls)} calls, {tokens:,} tokens, ${cost:.4f} (0 when the provider reports no cost)")


def main() -> None:
    """Parse arguments, run the agent on the toy task, and print a summary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="gemini", help="openrouter | gemini")
    parser.add_argument("--model", help="default: the provider's default in imle/llm.py")
    parser.add_argument("--effort", default="low", help="reasoning effort: low | medium | high")
    parser.add_argument("--minutes", type=float, default=10)
    parser.add_argument("--nodes", type=int, default=6)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true", help="canned replies instead of an LLM")
    parser.add_argument("--retrieval", choices=["static", "web"], default="static",
                        help="model cards: hand-written (default) or written by A2 from allowlisted docs")
    parser.add_argument("--resume", metavar="RUN_DIR", help="continue a smoke run from its latest checkpoint")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")

    if args.resume:
        run_dir = Path(args.resume).resolve()
        cfg = yaml.safe_load((run_dir / "config.yaml").read_text())
        seed = latest_complete_checkpoint(run_dir)["status"]["seed"]
        # A web run has its cards in model_cards.json, which the controller reuses; a static run has none.
        web = (run_dir / "model_cards.json").exists()
        retrieve = WebRetriever(ROOT / "data" / "retrieval_cache") if web else None
        controller = Controller.resume(run_dir, llm=make_llm(cfg, run_dir, seed), sandbox=SubprocessSandbox(),
                                       evaluator=ToyEvaluator(), retrieve=retrieve)
        summarise(run_dir, controller.run())
        return

    cfg = load_config(ROOT / "configs" / "conditions" / "c1_autonomous.yaml")
    cfg["budget"].update({"wall_clock_s": args.minutes * 60, "max_nodes": args.nodes, "script_timeout_s": 120})
    cfg["search"]["num_drafts"] = 2
    cfg["llm"].update({"provider": args.provider, "model": args.model or "", "effort": args.effort})
    cfg["sandbox"] = {"backend": "subprocess"}

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = "dry" if args.dry_run else args.provider
    run_dir = ROOT / "runs" / f"smoke_{name}_seed{args.seed}_{stamp}"
    llm = CannedLLM() if args.dry_run else make_llm(cfg, run_dir, args.seed)

    retrieve = WebRetriever(ROOT / "data" / "retrieval_cache") if args.retrieval == "web" else None
    controller = Controller(cfg, TASK, args.seed, run_dir, llm=llm, sandbox=SubprocessSandbox(),
                            evaluator=ToyEvaluator(), retrieve=retrieve)
    summarise(run_dir, controller.run())
    cards = run_dir / "model_cards.json"
    if cards.exists():
        report = json.loads(cards.read_text())
        print(f"A2: {len(report['cards'])} cards from {len(report['pages'])} pages, "
              f"{len(report['dropped'])} dropped, fallback={report['fallback']}")
        for c in report["cards"]:
            print(f"  - [{c['modality']}] {c['name']}")


if __name__ == "__main__":
    main()
