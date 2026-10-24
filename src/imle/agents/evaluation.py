"""A1: evaluation agent.

Runs once per run:
    - inspect data files and task description
    - build disjoint train / validation / probe splits
    - write the scoring harness, then freeze it (read-only to A3)

Runs per candidate script:
    - screen for target leakage and unused data sources before execution

The controller calls the module-level `prepare`, `score` and `screen`
(docs/core-agent-assumptions.md). The data layer, splits and metrics are the
stand-in evaluator's (imle.stand_in_evaluation), so every condition scores the same
rows as the C1 runs made with it. What A1 adds:

    <run_dir>/a1/harness.json    the frozen harness spec: task, metric, split sizes and
                                 the SHA-256 of every harness file
    <run_dir>/a1/harness.sha256  the spec's own hash
    <run_dir>/a1/context.json    the task context, so a repeated prepare returns it unchanged

`score` checks the hashes before every scoring, and `prepare` refuses to rebuild a
frozen harness. The harness lives outside the workspace, which is all the Docker
sandbox mounts, so A3's scripts cannot reach it there; with the subprocess sandbox
they could, and leakage rule R0 rejects scripts that try.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import stat
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from imle import stand_in_evaluation as data_layer
from imle.agents.coding import LLM

A1_DIR = "a1"
HARNESS_DIR = Path(data_layer.ROOT_DIR) / "harness"


class HarnessIntegrityError(Exception):
    """The frozen harness is missing, was changed, or a rebuild was attempted."""


# --------------------------------------------------------------------------- frozen harness


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def harness_files(run_dir: Path) -> dict[str, str]:
    """SHA-256 of every file in the harness folder, by path relative to the run folder."""
    root = run_dir / HARNESS_DIR
    if not root.is_dir():
        raise HarnessIntegrityError(f"{root} not found")
    return {str(p.relative_to(run_dir)): _sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def freeze(run_dir: Path, spec: dict[str, Any], context: dict[str, Any]) -> None:
    """Record the harness hashes and the context, then make the harness files read-only.

    Refuses if a frozen harness already exists: the harness is written once per run.
    """
    a1 = run_dir / A1_DIR
    if (a1 / "harness.sha256").exists():
        raise HarnessIntegrityError(f"harness already frozen in {a1}; it is never regenerated")
    spec = {**spec, "files": harness_files(run_dir)}
    a1.mkdir(parents=True, exist_ok=True)
    (a1 / "context.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
    (a1 / "harness.json").write_text(json.dumps(spec, indent=2, sort_keys=True), encoding="utf-8")
    for name in spec["files"]:
        path = run_dir / name
        path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    # Written last: its presence marks the harness as frozen.
    (a1 / "harness.sha256").write_text(hashlib.sha256(_canonical(spec)).hexdigest() + "\n", encoding="utf-8")


def verify(run_dir: Path) -> dict[str, Any]:
    """The frozen spec, after checking the spec hash and every file hash. Raises HarnessIntegrityError."""
    a1 = run_dir / A1_DIR
    try:
        spec = json.loads((a1 / "harness.json").read_text(encoding="utf-8"))
        expected = (a1 / "harness.sha256").read_text(encoding="utf-8").strip()
    except FileNotFoundError as e:
        raise HarnessIntegrityError(f"no frozen harness: {e.filename} missing") from e
    if hashlib.sha256(_canonical(spec)).hexdigest() != expected:
        raise HarnessIntegrityError("harness.json does not match harness.sha256")
    actual = harness_files(run_dir)
    if actual != spec["files"]:
        changed = sorted(set(actual.items()) ^ set(spec["files"].items()))
        raise HarnessIntegrityError(f"harness files changed since freezing: {sorted({c[0] for c in changed})}")
    return spec


def _config(run_dir: Path) -> dict:
    import yaml

    path = run_dir / "config.yaml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}


def _context(saved: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(**{**saved, "input_dir": Path(saved["input_dir"])})


# --------------------------------------------------------------------------- controller interface


def prepare(task: str, run_dir: Path, seed: int) -> SimpleNamespace:
    """Build the splits and the harness for `task` once, freeze the harness, and return the task context.

    The scoring mode comes from run_dir/config.yaml (`agents.evaluation`, see
    scoring_for) and is frozen with the harness. If the harness is already frozen (prepare called again after a crash), it is
    verified and the saved context is returned; nothing is rebuilt.
    """
    run_dir = Path(run_dir)
    if (run_dir / A1_DIR / "harness.sha256").exists():
        verify(run_dir)
        return _context(json.loads((run_dir / A1_DIR / "context.json").read_text(encoding="utf-8")))

    mode = scoring_for(_config(run_dir))
    ctx = mode.adjust(run_dir, task, data_layer.prepare(task, run_dir, seed))
    meta = json.loads((run_dir / HARNESS_DIR / "meta.json").read_text(encoding="utf-8"))
    context = {"description": ctx.description, "input_dir": str(ctx.input_dir),
               "prediction_format": ctx.prediction_format, "metric": ctx.metric,
               "higher_is_better": ctx.higher_is_better}
    spec = {"task": task, "mode": mode.name, "metric": ctx.metric, "higher_is_better": ctx.higher_is_better,
            "split_seed": meta["split_seed"], "rows": meta["rows"]}
    freeze(run_dir, spec, context)
    return _context(context)


def _error(message: str) -> SimpleNamespace:
    return SimpleNamespace(val_score=None, probe_score=None, test_score=None, error=message)


def score(node_dir: Path) -> SimpleNamespace:
    """Validation, probe and test scores of node_dir/output/predictions.csv, after verifying the harness.

    The scoring mode (A1 on or off) is the one frozen in the harness spec. Never raises:
    a changed harness, or missing or malformed predictions, come back as `error`.
    """
    node_dir = Path(node_dir)
    run_dir = node_dir.parent.parent
    try:
        spec = verify(run_dir)
    except HarnessIntegrityError as e:
        return _error(f"harness_integrity: {e}")
    return SCORING[spec.get("mode", HarnessScoring.name)].score(node_dir)


# --------------------------------------------------------------------------- scoring modes (A1 on / A1 off)


class HarnessScoring:
    """A1 on: validation and probe are both scored by the frozen harness."""

    name = "harness"

    def adjust(self, run_dir: Path, task: str, ctx: SimpleNamespace) -> SimpleNamespace:
        """The task context unchanged."""
        return ctx

    def score(self, node_dir: Path) -> SimpleNamespace:
        return data_layer.score(node_dir)


SELF_REPORT_FILE = "val_score.json"

SELF_REPORT_FORMAT = (
    " Also hold out part of train.csv yourself as a validation set, compute {metric} on it with the model the "
    "predictions come from, and write it to os.path.join(OUTPUT_DIR, \"{file}\") as {{\"val_score\": <number>}}. "
    "That number is the validation score this run uses to compare scripts."
)


class SelfReportScoring:
    """A1 off (the ablation): the script makes its own split and reports its own validation score.

    The validation rows rejoin train.csv, labelled, and leave predict.csv; the script
    writes OUTPUT_DIR/val_score.json. The probe rows stay in predict.csv and, like the
    test rows, are still scored by the frozen harness, so the probe is the same in
    every condition.
    """

    name = "self_report"

    def adjust(self, run_dir: Path, task: str, ctx: SimpleNamespace) -> SimpleNamespace:
        """Move the validation rows into train.csv and ask for a self-reported score."""
        import numpy as np
        import pandas as pd

        harness, inputs = run_dir / HARNESS_DIR, Path(ctx.input_dir)
        meta = json.loads((harness / "meta.json").read_text(encoding="utf-8"))
        as_str = {"id": str} if not meta["id_dtype"].startswith("int") else None
        labels = pd.read_csv(harness / "labels.csv", dtype=as_str, keep_default_na=False, na_values=[""])
        predict = pd.read_csv(inputs / "predict.csv", dtype=as_str)
        train = pd.read_csv(inputs / "train.csv", dtype=as_str)

        val = labels[labels["split"] == "val"]
        label_name = data_layer.TASKS[task].label_name
        val_labels = val[["id", *meta["label_cols"]]].rename(columns={"label": label_name} if label_name else {})
        val_rows = predict.merge(val_labels, on="id", how="inner")
        if len(val_rows) != len(val):
            raise HarnessIntegrityError(f"{len(val)} validation labels but {len(val_rows)} rows in predict.csv")
        combined = pd.concat([train, val_rows[train.columns]], ignore_index=True)
        order = np.random.default_rng(meta["split_seed"]).permutation(len(combined))
        combined.iloc[order].to_csv(inputs / "train.csv", index=False)
        predict[~predict["id"].isin(val["id"])].to_csv(inputs / "predict.csv", index=False)
        labels[labels["split"] != "val"].to_csv(harness / "labels.csv", index=False)

        fmt = ctx.prediction_format + SELF_REPORT_FORMAT.format(metric=ctx.metric, file=SELF_REPORT_FILE)
        return SimpleNamespace(**{**vars(ctx), "prediction_format": fmt})

    def score(self, node_dir: Path) -> SimpleNamespace:
        import pandas as pd

        if not (node_dir / "output" / "predictions.csv").exists():
            return _error("predictions.csv not found")
        try:
            reported = json.loads((node_dir / "output" / SELF_REPORT_FILE).read_text(encoding="utf-8"))
            val = float(reported["val_score"])
            if not math.isfinite(val):
                raise ValueError("val_score is not a finite number")
        except FileNotFoundError:
            return _error(f"{SELF_REPORT_FILE} not found: the script must report its own validation score")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            return _error(f"{SELF_REPORT_FILE} is invalid: {str(e)[:200]}")
        try:
            joined, meta = data_layer.labelled_predictions(node_dir)
            probe = data_layer.metric(joined[joined.split == "probe"], meta)
            test = data_layer.metric(joined[joined.split == "test"], meta)
            # The stand-in's own submission writer, so the file is in MLE-bench's format (interface request 2).
            data_layer._submission(joined, meta, node_dir.parent.parent / HARNESS_DIR).to_csv(
                node_dir / "submission.csv", index=False)
        except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as e:
            return _error(str(e)[:500])
        return SimpleNamespace(val_score=val, probe_score=probe, test_score=test, error=None)


SCORING = {HarnessScoring.name: HarnessScoring(), SelfReportScoring.name: SelfReportScoring()}


def scoring_for(cfg: dict) -> HarnessScoring | SelfReportScoring:
    """The scoring mode for a run config: self-report when `agents.evaluation` is false (A1-off)."""
    on = bool((cfg.get("agents") or {}).get("evaluation", True))
    return SCORING[HarnessScoring.name if on else SelfReportScoring.name]


def screen(llm: LLM, script: str) -> str | None:
    """The controller's leakage check: a reason if the rules find a leak, else None.

    Rules only, so the live screen is deterministic and costs no tokens; `llm` is
    accepted for the controller's signature. Warnings do not reject the script.
    """
    report = screen_script(script)
    leaks = [f for f in report.flags if f.severity == Severity.LEAK]
    return "; ".join(f"{f.rule} (line {f.line}): {f.detail}" for f in leaks) or None


# --------------------------------------------------------------------------- leakage screen


class Severity(str, Enum):
    WARN = "warn"   # recorded and counted, but the script runs
    LEAK = "leak"   # the script is rejected


class Flag(BaseModel):
    rule: str        # R0_harness_access | R1_target_as_feature | R2_test_statistics | R3_val_in_training | llm
    severity: Severity
    line: int | None = None
    detail: str
    source: str = "rules"   # rules | llm


class LeakageReport(BaseModel):
    flags: list[Flag]
    verdict: str            # clean | warn | leak
    target: str | None      # the target column the rules used, if one was found

    @classmethod
    def of(cls, flags: list[Flag], target: str | None) -> LeakageReport:
        severities = {f.severity for f in flags}
        verdict = "leak" if Severity.LEAK in severities else "warn" if severities else "clean"
        return cls(flags=sorted(flags, key=lambda f: (f.line or 0, f.rule)), verdict=verdict, target=target)


class ReviewReply(BaseModel):
    """The LLM review's answer."""

    leak: bool
    kind: str                # target_as_feature | test_statistics | val_in_training | harness_access | none
    line: int | None = None
    reason: str


_FORBIDDEN_PATH = re.compile(
    r"harness|labels\.csv|stand_in|mle-?bench|mle_bench|(^|[/\\])private([/\\]|$)|(^|[/\\])\.\.([/\\]|$)",
    re.IGNORECASE,
)
_NOT_FILE_CALLS = {"print", "format", "info", "debug", "warning", "error", "write", "log"}
_SUPERVISED = {"fit"}
_STAT_METHODS = {"mean", "median", "std", "var", "mode", "min", "max", "quantile"}
_PREDICT_METHODS = {"predict", "predict_proba", "predict_log_proba", "decision_function", "score"}
# Methods that return the same columns as their receiver (row selection, cleaning, conversion).
_SAME_COLUMNS = {"copy", "fillna", "reset_index", "sample", "dropna", "sort_values", "head", "tail", "astype",
                 "to_numpy", "infer_objects", "replace"}


def _call_name(call: ast.Call) -> str:
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _str_list(node: ast.AST | None) -> list[str] | None:
    """The strings of a list or tuple literal of string constants, or of a single string constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.List, ast.Tuple)) and all(
            isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts):
        return [e.value for e in node.elts]
    return None


class _Analysis:
    """A flow-ordered pass over a script: which variables hold the training frame, predict rows or validation rows."""

    def __init__(self, tree: ast.Module, target: str | None):
        self.tree = tree
        self.bindings: dict[str, ast.AST] = {}     # latest assignment per name, in source order
        self.taint: dict[str, set[str]] = {}        # name -> {"train", "predict", "val"}
        self.target = target
        self.flags: list[Flag] = []

    # ---- data flow

    def expr_taint(self, node: ast.AST) -> set[str]:
        """Origins of the data an expression holds: train.csv, predict.csv, or a validation split.

        A model's predictions and a fitted model carry no taint: they are not rows of data.
        """
        if isinstance(node, ast.Name):
            return set(self.taint.get(node.id, set()))
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in _PREDICT_METHODS or name == "fit":
                return set()
            if name in {"read_csv", "read_parquet", "read_json"}:
                out: set[str] = set()
                for c in (c for arg in node.args[:1] for c in ast.walk(arg)):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str):
                        if "predict" in c.value or "test" in c.value:
                            out.add("predict")
                        elif "train" in c.value:
                            out.add("train")
                return out
        out = set()
        for child in ast.iter_child_nodes(node):
            out |= self.expr_taint(child)
        return out

    def resolve(self, node: ast.AST, depth: int = 0) -> ast.AST:
        """Follow a bare name to the expression last assigned to it."""
        while isinstance(node, ast.Name) and node.id in self.bindings and depth < 10:
            node, depth = self.bindings[node.id], depth + 1
        return node

    def has_target_columns(self, node: ast.AST, depth: int = 0) -> bool:
        """Whether an expression provably still holds the target column of the training frame."""
        if depth > 10 or self.target is None:
            return False
        node = self.resolve(node)
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in {"read_csv", "read_parquet", "read_json"}:
                return self.expr_taint(node) == {"train"}
            if name == "concat" and node.args:
                parts = node.args[0].elts if isinstance(node.args[0], (ast.List, ast.Tuple)) else []
                return any(self.has_target_columns(p, depth + 1) for p in parts)
            if isinstance(node.func, ast.Attribute):
                receiver = node.func.value
                if name in _SAME_COLUMNS:
                    return self.has_target_columns(receiver, depth + 1)
                if name == "drop":
                    dropped = self._dropped_columns(node)
                    return dropped is not None and self.target not in dropped and \
                        self.has_target_columns(receiver, depth + 1)
            return False
        if isinstance(node, ast.Attribute) and node.attr == "values":
            return self.has_target_columns(node.value, depth + 1)
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Attribute) and node.value.attr in {"iloc", "loc"}:
                index = node.slice
                if isinstance(index, ast.Tuple):  # .loc[rows, cols]
                    cols = _str_list(self.resolve(index.elts[1])) if len(index.elts) > 1 else None
                    return cols is not None and self.target in cols
                return self.has_target_columns(node.value.value, depth + 1)
            # df[["a", "author"]] keeps the target; df["author"] is the target itself, not a feature frame.
            index = self.resolve(node.slice)
            cols = _str_list(index) if isinstance(index, (ast.List, ast.Tuple)) else None
            return cols is not None and self.target in cols
        return False

    def _dropped_columns(self, call: ast.Call) -> list[str] | None:
        """The columns a .drop() call removes, when they are written as literals."""
        for kw in call.keywords:
            if kw.arg == "columns":
                return _str_list(self.resolve(kw.value))
        axis_one = any(kw.arg == "axis" and isinstance(kw.value, ast.Constant) and kw.value.value in (1, "columns")
                       for kw in call.keywords)
        if call.args and (axis_one or (len(call.args) > 1)):
            return _str_list(self.resolve(call.args[0]))
        return None if call.args or call.keywords else []

    def find_target(self) -> None:
        """The column assigned to y (or a name with target or label in it) from a frame, if the rules can see it."""
        if self.target is not None:
            return

        def rank(name: str) -> int | None:
            """0 for y and y_train, 1 for other target-like names, None for anything else (or predictions)."""
            if "pred" in name or "val" in name or "test" in name:
                return None
            if name in {"y", "y_train", "target", "labels", "label"}:
                return 0
            return 1 if name.startswith("y_") or "target" in name or "label" in name else None

        candidates = sorted(
            ((r, node.lineno, node) for node in ast.walk(self.tree)
             if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
             and (r := rank(node.targets[0].id.lower())) is not None),
            key=lambda c: (c[0], c[1]))
        for _, _, node in candidates:
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.Constant) \
                        and isinstance(sub.slice.value, str):
                    self.target = sub.slice.value
                    return

    def assign(self, node: ast.Assign) -> None:
        """Record what an assignment binds, including the outputs of train_test_split."""
        value_taint = self.expr_taint(node.value)
        is_split = isinstance(node.value, ast.Call) and _call_name(node.value) == "train_test_split"
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.bindings[target.id] = node.value
                self.taint[target.id] = set(value_taint)
            elif isinstance(target, (ast.Tuple, ast.List)):
                names = [e.id if isinstance(e, ast.Name) else None for e in target.elts]
                for i, name in enumerate(names):
                    if name is None:
                        continue
                    self.taint[name] = set(value_taint)
                    if is_split:
                        # train_test_split returns (a_train, a_test, b_train, b_test, ...): odd positions are held out.
                        source = node.value.args[i // 2] if i // 2 < len(node.value.args) else None
                        self.bindings[name] = source if (source is not None and i % 2 == 0) else node.value
                        if i % 2 == 1:
                            self.taint[name].add("val")
                    else:
                        self.bindings.pop(name, None)

    # ---- rules

    def r0_paths(self) -> None:
        for call in ast.walk(self.tree):
            if not isinstance(call, ast.Call) or _call_name(call) in _NOT_FILE_CALLS:
                continue
            for arg in [*call.args, *(kw.value for kw in call.keywords)]:
                for c in ast.walk(arg):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str) and _FORBIDDEN_PATH.search(c.value):
                        self.flags.append(Flag(rule="R0_harness_access", severity=Severity.LEAK, line=c.lineno,
                                               detail=f"reads outside ./input: {c.value!r}"))
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Attribute) and node.attr == "parent" and isinstance(node.value, ast.Attribute) \
                    and node.value.attr == "parent":
                self.flags.append(Flag(rule="R0_harness_access", severity=Severity.LEAK, line=node.lineno,
                                       detail="walks up out of the working directory (.parent.parent)"))

    def r1_r2_r3(self, statements: list[ast.stmt]) -> None:
        fitted_on_val: dict[str, int] = {}   # model name -> line of a fit that included validation rows
        for node in statements:
            if isinstance(node, ast.Assign):
                self.check_calls(node.value, fitted_on_val)
                self.assign(node)
            elif isinstance(node, (ast.Expr, ast.AugAssign, ast.AnnAssign, ast.Return)) and node.value is not None:
                self.check_calls(node.value, fitted_on_val)

    def check_calls(self, expr: ast.AST, fitted_on_val: dict[str, int]) -> None:
        for call in ast.walk(expr):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue
            name, receiver = call.func.attr, call.func.value
            x = call.args[0] if call.args else None
            supervised = name in _SUPERVISED and (len(call.args) >= 2 or any(k.arg == "y" for k in call.keywords))
            if supervised and x is not None and self.has_target_columns(x):
                self.flags.append(Flag(rule="R1_target_as_feature", severity=Severity.LEAK, line=call.lineno,
                                       detail=f"the target column {self.target!r} is among the features passed to fit"))
            if name in {"fit", "fit_transform"} and x is not None and not supervised \
                    and "predict" in self.expr_taint(x):
                self.flags.append(Flag(rule="R2_test_statistics", severity=Severity.WARN, line=call.lineno,
                                       detail="a transformer is fitted on rows from predict.csv"))
            if name in _STAT_METHODS and "predict" in self.expr_taint(receiver):
                self.flags.append(Flag(rule="R2_test_statistics", severity=Severity.WARN, line=call.lineno,
                                       detail=f".{name}() is computed on rows from predict.csv"))
            if supervised and x is not None and "val" in self.expr_taint(x) and isinstance(receiver, ast.Name):
                fitted_on_val[receiver.id] = call.lineno
            if name in _PREDICT_METHODS and isinstance(receiver, ast.Name) and receiver.id in fitted_on_val \
                    and x is not None and "val" in self.expr_taint(x):
                self.flags.append(Flag(
                    rule="R3_val_in_training", severity=Severity.LEAK, line=call.lineno,
                    detail=f"{receiver.id} is evaluated on validation rows it was fitted on "
                           f"(fit at line {fitted_on_val[receiver.id]})"))


def _ordered_statements(tree: ast.Module) -> list[ast.stmt]:
    """Every simple statement in the script, including those inside functions and blocks, in source order."""
    out = [n for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.Expr, ast.AugAssign, ast.AnnAssign,
                                                       ast.Return))]
    return sorted(out, key=lambda n: (n.lineno, n.col_offset))


REVIEW_SYSTEM = "You review machine learning scripts for data leakage. You answer with one JSON object only."

REVIEW_PROMPT = """\
The script below trains on input/train.csv (labelled) and predicts input/predict.csv
(unlabelled; the labels are held by a harness the script must not read). Decide whether
it leaks: the target used as a feature, statistics computed on predict.csv or on the
combined data before splitting, validation rows used to fit the model it then
validates, or reading files outside ./input. Unsupervised use of predict.csv text
(for example fitting a vectorizer on all text) counts as test_statistics.

Answer with exactly this JSON object:
{{"leak": true or false, "kind": "target_as_feature" | "test_statistics" | "val_in_training" | "harness_access" | "none",
  "line": line number or null, "reason": "one sentence"}}

```python
{script}
```"""


def screen_script(script_text: str, task_meta: dict[str, Any] | None = None, llm: LLM | None = None,
                  max_retries: int = 2) -> LeakageReport:
    """Screen a script for leakage with deterministic rules, then optionally an LLM review.

    Rules (false positives are the main cost, so each fires only on a pattern it can prove):
        R0 harness access (leak): a file path naming the harness, labels.csv, MLE-bench,
           a private folder, or a parent folder.
        R1 target as feature (leak): a supervised fit whose features provably still hold the
           target column (whole frame, a literal column list, or a drop that keeps it).
           The target comes from `task_meta["target"]`, else from the script's `y = df["col"]`.
        R2 test statistics (warn): a transformer fitted, or a mean/median/std/... computed,
           on rows from predict.csv. MLE-bench allows this kind of unsupervised use, so it
           does not reject the script.
        R3 validation rows in training (leak): a model fitted on rows from a validation split,
           then evaluated on validation rows.

    With `llm`, the review's answer is added as one more flag (source "llm"). A script
    that does not parse gets no flags: the sandbox reports the syntax error.
    """
    target = (task_meta or {}).get("target")
    try:
        tree = ast.parse(script_text)
    except SyntaxError:
        return LeakageReport.of([], target)
    analysis = _Analysis(tree, target)
    analysis.find_target()
    analysis.r0_paths()
    analysis.r1_r2_r3(_ordered_statements(tree))
    flags = list({(f.rule, f.line, f.detail): f for f in analysis.flags}.values())

    if llm is not None:
        from imle.agents.reflection import ask_json

        reply = ask_json(llm, agent="evaluation", system=REVIEW_SYSTEM,
                         user=REVIEW_PROMPT.format(script=script_text), schema=ReviewReply, max_retries=max_retries)
        if reply.leak:
            flags.append(Flag(rule="llm", severity=Severity.LEAK, line=reply.line,
                              detail=f"{reply.kind}: {reply.reason}", source="llm"))
    return LeakageReport.of(flags, analysis.target)
