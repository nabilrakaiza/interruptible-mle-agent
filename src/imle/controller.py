"""A5: tree controller and main loop.

Responsibilities:
    - select the next node and operator (greedy on validation score to start)
    - enforce stopping rules (budget, node cap, debug depth, improve stagnation)
    - checkpoint at every safe point
    - drain the intervention queue and apply or drop each action
    - choose the final submission (best-val, top-k, or human override)

The controller is the ONLY writer to the tree.

Implemented so far: draft-only search, budget and node-cap stopping,
checkpointing, best-val final selection. The sandbox, LLM and evaluator are
passed in; the signatures assumed here are in docs/core-agent-assumptions.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import time
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any, Protocol

import yaml
from dotenv import load_dotenv

from imle import checkpoint
from imle.agents import coding
from imle.agents.coding import LLM, CodingError, TaskContext
from imle.tree import Node, NodeStatus, Operator, Tree

ERROR_TAIL_CHARS = 2000


class ExecResult(Protocol):
    """What the sandbox reports for one script execution. Defined by role 1."""

    stdout: str
    stderr: str
    exit_code: int
    wall_time_s: float
    timed_out: bool


class SandboxRun(Protocol):
    """The sandbox entry point, sandbox.run. Implemented by role 1."""

    def __call__(self, script_path: Path, cwd: Path, timeout_s: float) -> ExecResult:
        """Execute `script_path` with `cwd` as its working directory and kill it after `timeout_s`.

        A timeout or a crash is reported in the result, never raised.
        """
        ...


class ScoreResult(Protocol):
    """Scores for one node's predictions. Defined by role 3."""

    val_score: float | None
    probe_score: float | None
    error: str | None         # set when predictions are missing or malformed


class Evaluator(Protocol):
    """A1 as the controller sees it, agents/evaluation.py. Implemented by role 3."""

    def prepare(self, task: str, run_dir: Path, seed: int) -> TaskContext:
        """Build the train / validation / probe splits for `task`, once per run.

        Returns what A3 needs to write a script: the description, the input folder,
        the prediction format and the metric.
        """
        ...

    def score(self, node_dir: Path) -> ScoreResult:
        """Score `node_dir/predictions.csv` on validation and probe.

        Also writes the test rows to `node_dir/submission.csv`. Missing or malformed
        predictions come back as `error`, never as an exception.
        """
        ...


def _now() -> str:
    """Current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _merge(base: dict, override: dict) -> dict:
    """Deep-merge two dicts. Values in `override` win."""
    out = dict(base)
    for k, v in override.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _expand_env(value: Any) -> Any:
    """Replace ${VAR} with its environment value in every string of a nested config."""
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return os.path.expandvars(value) if isinstance(value, str) else value


def load_config(condition_path: Path) -> dict:
    """configs/base.yaml overridden by one condition file, with ${VAR} expanded."""
    base_path = condition_path.resolve().parent.parent / "base.yaml"
    base = yaml.safe_load(base_path.read_text(encoding="utf-8")) or {}
    condition = yaml.safe_load(condition_path.read_text(encoding="utf-8")) or {}
    return _expand_env(_merge(base, condition))


def select_next(tree: Tree, cfg: dict) -> tuple[Operator, str | None] | None:
    """The next (operator, parent id), or None when the search has nothing left to try.

    A pure function of the tree, so a prune or a resume needs no extra bookkeeping.
    """
    drafts = sum(1 for n in tree.nodes.values() if n.operator == Operator.DRAFT)
    if drafts < cfg["search"]["num_drafts"]:
        return Operator.DRAFT, None
    return None


class Controller:
    """One search run. Owns the tree and everything written under the run folder."""

    def __init__(
        self,
        cfg: dict,
        task: str,
        seed: int,
        run_dir: Path,
        *,
        llm: LLM,
        sandbox_run: SandboxRun,
        evaluator: Evaluator,
    ) -> None:
        """Store the run settings and the three injected dependencies, and start the budget clock."""
        self.cfg = cfg
        self.task = task
        self.seed = seed
        self.run_dir = run_dir
        self.llm = llm
        self.sandbox_run = sandbox_run
        self.evaluator = evaluator
        self.tree = Tree()
        self.findings: list = []
        self.step = 0
        self._t0 = time.monotonic()

    def elapsed_s(self) -> float:
        """Seconds since the run started."""
        return time.monotonic() - self._t0

    def remaining_s(self) -> float:
        """Seconds of wall-clock budget left. Negative once the budget is spent."""
        return self.cfg["budget"]["wall_clock_s"] - self.elapsed_s()

    def script_timeout_s(self) -> float:
        """Timeout for the next script: the configured limit or the remaining budget, whichever is smaller."""
        return max(1.0, min(self.cfg["budget"]["script_timeout_s"], self.remaining_s()))

    def stop_reason(self) -> str | None:
        """Why the search must stop now ("budget" or "max_nodes"), or None to keep going."""
        if self.remaining_s() <= 0:
            return "budget"
        if len(self.tree.nodes) >= self.cfg["budget"]["max_nodes"]:
            return "max_nodes"
        return None

    def run(self) -> Tree:
        """Run the whole search and return the finished tree.

        Prepares the task, adds nodes until a stopping rule fires, then chooses the final submission.
        """
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "config.yaml").write_text(yaml.safe_dump(self.cfg), encoding="utf-8")

        self.ctx = self.evaluator.prepare(self.task, self.run_dir, self.seed)
        self.tree.higher_is_better = self.ctx.higher_is_better
        self.safe_point(current_node=None)

        while (reason := self.stop_reason()) is None:
            choice = select_next(self.tree, self.cfg)
            if choice is None:
                reason = "search_exhausted"
                break
            node = self.run_node(*choice)
            self.safe_point(current_node=node.id)

        self.finalize(reason)
        return self.tree

    def run_node(self, operator: Operator, parent_id: str | None) -> Node:
        """Create one node: generate a script, execute it, score it, record the result.

        A failure at any stage gives a buggy node with a categorised error, not an exception.
        """
        node = Node(id=f"n{len(self.tree.nodes)}", parent_id=parent_id, operator=operator, started_at=_now())
        self.tree.add(node)
        node_dir = self.run_dir / "nodes" / node.id
        node_dir.mkdir(parents=True)

        try:
            node.plan, script = coding.draft(self.llm, self.ctx, self.script_timeout_s())
        except CodingError as e:
            return self._close(node, error=f"generation_error: {e}")

        script_path = node_dir / "solution.py"
        script_path.write_text(script, encoding="utf-8")
        node.script_path = str(script_path)
        # Relative, so the link survives the run folder being moved to shared storage.
        target = os.path.relpath(Path(self.ctx.input_dir).resolve(), node_dir.resolve())
        (node_dir / "input").symlink_to(target, target_is_directory=True)

        # Recomputed: generating the script used some of the budget.
        timeout_s = self.script_timeout_s()
        result = self.sandbox_run(script_path, node_dir, timeout_s)
        (node_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (node_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        if result.timed_out:
            return self._close(node, error=f"timeout: killed after {timeout_s:.0f}s")
        if result.exit_code != 0:
            tail = result.stderr[-ERROR_TAIL_CHARS:].strip()
            return self._close(node, error=f"runtime_error: exit code {result.exit_code}\n{tail}")

        score = self.evaluator.score(node_dir)
        if score.error is not None or score.val_score is None:
            return self._close(node, error=f"invalid_submission: {score.error or 'no validation score'}")
        node.val_score = score.val_score
        node.probe_score = score.probe_score
        return self._close(node)

    def _close(self, node: Node, error: str | None = None) -> Node:
        """Mark a node finished: working if there is no error, buggy otherwise."""
        node.error = error
        node.status = NodeStatus.WORKING if error is None else NodeStatus.BUGGY
        node.finished_at = _now()
        return node

    def safe_point(self, current_node: str | None, **extra: Any) -> None:
        """Write a checkpoint of the tree, findings and run status.

        Extra keyword arguments are added to status.json.
        """
        status = {
            "current_node": current_node,
            "elapsed_s": round(self.elapsed_s(), 1),
            "timestamp": _now(),
            "task": self.task,
            "seed": self.seed,
            "condition": self.cfg.get("condition"),
            "done": False,
            **extra,
        }
        checkpoint.write(self.run_dir, self.step, self.tree.model_dump(mode="json"), self.findings, status)
        self.step += 1
        # TODO: drain the queue and apply interventions here (16 to 18 Oct).

    def finalize(self, reason: str) -> None:
        """Choose the final node, copy its submission into the run folder, write the last checkpoint."""
        mode = self.cfg["final_selection"]
        if mode != "best_val":
            raise NotImplementedError(f"final_selection={mode}")
        best = self.tree.best_by_val()
        submitted = False
        if best is not None:
            src = self.run_dir / "nodes" / best.id / "submission.csv"
            if src.exists():
                shutil.copyfile(src, self.run_dir / "submission.csv")
                submitted = True
        self.safe_point(
            current_node=None,
            done=True,
            stop_reason=reason,
            final_node=best.id if best else None,
            submitted=submitted,
        )


def main() -> None:
    """Command-line entry point: load the config, wire in the real sandbox, LLM and evaluator, run."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--run-dir", help="default: runs/<condition>_<task>_seed<seed>_<utc time>")
    args = parser.parse_args()

    load_dotenv()
    cfg = load_config(Path(args.config))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    default_name = f"{cfg.get('condition', 'run')}_{args.task}_seed{args.seed}_{stamp}"
    run_dir = Path(args.run_dir) if args.run_dir else Path("runs") / default_name

    from imle import llm_log, sandbox
    from imle.agents import evaluation

    for module, names in ((sandbox, ["run"]), (llm_log, ["complete"]), (evaluation, ["prepare", "score"])):
        for name in names:
            if not hasattr(module, name):
                raise SystemExit(
                    f"{module.__name__}.{name} is not implemented yet. "
                    "Expected signature: docs/core-agent-assumptions.md"
                )

    llm = partial(
        llm_log.complete,
        model=cfg["llm"]["model"],
        temperature=cfg["llm"]["temperature"],
        seed=args.seed,
        run_dir=run_dir,
    )
    Controller(cfg, args.task, args.seed, run_dir, llm=llm, sandbox_run=sandbox.run, evaluator=evaluation).run()
    print(f"run finished: {run_dir}")


if __name__ == "__main__":
    main()
