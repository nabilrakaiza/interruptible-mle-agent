"""A5: tree controller and main loop.

Responsibilities:
    - select the next node and operator (greedy on validation score to start)
    - enforce stopping rules (budget, node cap, debug depth, improve stagnation)
    - checkpoint at every safe point
    - drain the intervention queue and apply or drop each action
    - choose the final submission (best-val, top-k, or human override)

The controller is the ONLY writer to the tree.

The sandbox, LLM, evaluator, retrieval and reflection agents are passed in. The signatures
assumed for the parts owned by other roles are in docs/core-agent-assumptions.md.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

from imle import checkpoint
from imle.agents import coding, retrieval
from imle.agents.coding import LLM, CodingError, LLMUnavailable, TaskContext
from imle.apply import apply_pending
from imle.state import SearchState
from imle.tree import Node, NodeStatus, Operator, Tree


class ExecResult(Protocol):
    """What the sandbox reports for one script execution. Defined by role 1."""

    stdout: str
    stderr: str
    exit_code: int
    wall_time_s: float
    timed_out: bool


class Sandbox(Protocol):
    """A sandbox backend. See imle.execution."""

    def output_path(self, output_dir: Path) -> str:
        """The path the script must write to for its output to land in `output_dir`."""
        ...

    def run(self, script_path: Path, workspace: Path, output_dir: Path, timeout_s: float) -> ExecResult:
        """Execute `script_path` with `workspace` as its read-only working directory.

        Kills it after `timeout_s`. A timeout or a crash is reported in the result, never raised.
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
        """Score `node_dir/output/predictions.csv` on validation and probe.

        Also writes the test rows to `node_dir/submission.csv`. Missing or malformed
        predictions come back as `error`, never as an exception. Must also work in a
        new process after a crash, from what `prepare` saved under the run folder.
        """
        ...


class Retrieve(Protocol):
    """A2, agents/retrieval.py `WebRetriever`. Optional; without it the hand-written cards are used."""

    def __call__(self, llm: LLM, task: str, ctx: TaskContext, run_dir: Path) -> list[dict]:
        """Return the model cards for the run, and save them with an audit report to run_dir/model_cards.json."""
        ...


class Reflect(Protocol):
    """A4, agents/reflection.py `reflect`. Implemented by role 3. Optional."""

    def __call__(self, llm: LLM, tree: Tree, findings: list[dict], run_dir: Path) -> list[dict]:
        """Return the findings after the latest node: unchanged, or updated if a phase closed."""
        ...


class SavedContext(BaseModel):
    """The task context as saved to task_context.json, so a resumed run does not rebuild the splits."""

    description: str
    input_dir: Path
    prediction_format: str
    metric: str
    higher_is_better: bool


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


def _link_tree(src: Path, dst: Path) -> None:
    """Copy a folder by hard-linking its files, falling back to real copies across filesystems."""

    def link_or_copy(s: str, d: str) -> None:
        """Hard-link one file, or copy it if linking is not possible."""
        try:
            os.link(s, d)
        except OSError:
            shutil.copy2(s, d)

    shutil.copytree(src, dst, copy_function=link_or_copy)


def debug_depth(tree: Tree, node: Node) -> int:
    """How many debug attempts in a row led to this node (0 for a draft or improve)."""
    depth = 0
    while node.operator == Operator.DEBUG:
        depth += 1
        node = tree.nodes[node.parent_id]
    return depth


def beats(tree: Tree, new: float, old: float, min_rel_gain: float) -> bool:
    """Whether `new` improves on `old` by at least `min_rel_gain`, relative to |old|."""
    gain = (new - old) if tree.higher_is_better else (old - new)
    return gain >= min_rel_gain * max(abs(old), 1e-12)


def improve_failures(tree: Tree, search: dict) -> dict[str, int]:
    """For each node, the failed improve attempts on its improve chain.

    An improve that does not beat its parent by improve_min_rel_gain (worse, buggy, or
    better by only a little) is a failed attempt and stays in its parent's chain. An
    improve that does beat it starts a new chain. Every node in a chain shares the chain's
    count, so once it reaches improve_patience the whole chain is exhausted.

    Before, the count was per node, so a run of tiny gains (0.12738, 0.12736, ...) never
    ran out of patience: each new node was the best by raw score and started at zero. This
    follows the proposal (Section 3.6): an improve chain ends after a fixed number of
    attempts below the relative threshold.
    """
    gain = search["improve_min_rel_gain"]
    chain: dict[str, str] = {}  # node id -> id of the node that started its chain
    failed: dict[str, int] = {}
    for n in tree.nodes.values():  # creation order: a parent always comes before its children
        parent = tree.nodes.get(n.parent_id) if n.parent_id else None
        stays = (n.operator == Operator.IMPROVE and parent is not None and parent.val_score is not None
                 and (n.val_score is None or not beats(tree, n.val_score, parent.val_score, gain)))
        if stays:
            chain[n.id] = chain[parent.id]
            failed[chain[n.id]] += 1
        else:
            chain[n.id] = n.id
            failed[n.id] = 0
    return {node_id: failed[start] for node_id, start in chain.items()}


def improve_exhausted(tree: Tree, node: Node, search: dict) -> bool:
    """Whether `node`'s improve chain has had `improve_patience` attempts that failed to beat it."""
    return improve_failures(tree, search)[node.id] >= search["improve_patience"]


def debuggable(tree: Tree, search: dict) -> list[Node]:
    """Buggy leaves that have a script and have not reached `max_debug_depth`."""
    return [
        n
        for n in tree.nodes.values()
        if n.status == NodeStatus.BUGGY
        and n.script_path
        and not tree.children(n.id)
        and debug_depth(tree, n) < search["max_debug_depth"]
    ]


def ranked(tree: Tree) -> list[Node]:
    """Working nodes with a validation score, best first."""
    nodes = [n for n in tree.selectable() if n.val_score is not None]
    return sorted(nodes, key=lambda n: n.val_score, reverse=tree.higher_is_better)


def select_next(tree: Tree, search: dict, rng: random.Random) -> tuple[Operator, str | None]:
    """The next (operator, parent id), following the AIDE-style greedy policy.

    1. Draft until `num_drafts` drafts exist.
    2. With probability `debug_prob`, debug a random buggy leaf below `max_debug_depth`.
    3. Otherwise improve the best working node that is not exhausted (see improve_failures).
    4. With nothing to improve, debug if possible, else draft again.

    A pure function of the tree and the random state, so a prune or a resume needs
    no extra bookkeeping.
    """
    if search.get("policy", "greedy") != "greedy":
        raise ValueError(f"unknown search policy {search['policy']!r}")
    drafts = sum(1 for n in tree.nodes.values() if n.operator == Operator.DRAFT)
    if drafts < search["num_drafts"]:
        return Operator.DRAFT, None

    to_debug = debuggable(tree, search)
    if to_debug and rng.random() < search["debug_prob"]:
        return Operator.DEBUG, rng.choice(to_debug).id

    failures = improve_failures(tree, search)
    for node in ranked(tree):
        if failures[node.id] < search["improve_patience"]:
            return Operator.IMPROVE, node.id

    if to_debug:
        return Operator.DEBUG, rng.choice(to_debug).id
    return Operator.DRAFT, None


def latest_complete_checkpoint(run_dir: Path) -> dict | None:
    """The newest checkpoint that was fully written, skipping one cut short by a crash."""
    step = checkpoint.latest_step(run_dir)
    while step is not None and step >= 0:
        ck = checkpoint.read(run_dir, step)
        if ck is not None:
            return ck
        step -= 1
    return None


def _rng_state_to_json(state: tuple) -> list:
    """random.Random state as JSON-friendly lists."""
    version, internal, gauss = state
    return [version, list(internal), gauss]


def _rng_state_from_json(state: list) -> tuple:
    """random.Random state back from its JSON form."""
    version, internal, gauss = state
    return version, tuple(internal), gauss


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
        sandbox: Sandbox,
        evaluator: Evaluator,
        reflect: Reflect | None = None,
        retrieve: Retrieve | None = None,
    ) -> None:
        """Store the run settings and dependencies, and start the budget clock."""
        self.cfg = cfg
        self.task = task
        self.seed = seed
        self.run_dir = Path(run_dir)
        self.llm = llm
        self.sandbox = sandbox
        self.evaluator = evaluator
        self.reflect = reflect
        self.retrieve = retrieve
        self._cards: list[dict] | None = None
        self.tree = Tree()
        self.findings: list[dict] = []
        self.state = SearchState()
        self.rng = random.Random(seed)
        self.ctx: SavedContext | None = None
        self.done = False
        self._elapsed_before = 0.0
        self._paused_s = 0.0  # time lost to LLM outages, not charged to the budget
        self._t0 = time.monotonic()
        self._sleep = time.sleep  # replaced in tests

    @classmethod
    def resume(cls, run_dir: Path, **deps: Any) -> Controller:
        """Rebuild a controller from the latest complete checkpoint of `run_dir`.

        `deps` are the same keyword arguments as the constructor (llm, sandbox, evaluator,
        reflect, retrieve). Time between the crash and the resume is not charged to the budget.
        """
        run_dir = Path(run_dir)
        ck = latest_complete_checkpoint(run_dir)
        if ck is None:
            raise ValueError(f"{run_dir} has no complete checkpoint to resume from")
        status = ck["status"]
        cfg = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
        c = cls(cfg, status["task"], status["seed"], run_dir, **deps)
        c.tree = Tree.model_validate(ck["tree"])
        c.findings = ck["findings"]
        c.state = SearchState.model_validate(status["search"])
        c.state.step = ck["step"] + 1
        if c.state.rng_state is not None:
            c.rng.setstate(_rng_state_from_json(c.state.rng_state))
        c.ctx = SavedContext.model_validate_json((run_dir / "task_context.json").read_text(encoding="utf-8"))
        c.done = bool(status.get("done"))
        c._elapsed_before = c.state.elapsed_s
        c._set_aside_unfinished_nodes()
        c._set_aside_incomplete_checkpoints(ck["step"])
        return c

    @property
    def workspace(self) -> Path:
        """The sandbox's working directory: every node's script plus the input data."""
        return self.run_dir / "workspace"

    def node_dir(self, node_id: str) -> Path:
        """Where one node's script, logs, output and submission live."""
        return self.run_dir / "nodes" / node_id

    def elapsed_s(self) -> float:
        """Seconds of budget used, including time before a resume and excluding LLM outages."""
        return self._elapsed_before + time.monotonic() - self._t0 - self._paused_s

    def remaining_s(self) -> float:
        """Seconds of wall-clock budget left, after rebudgets. Negative once it is spent."""
        return self.cfg["budget"]["wall_clock_s"] + self.state.extra_budget_s - self.elapsed_s()

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

    def agent_on(self, name: str) -> bool:
        """Whether an optional agent (evaluation, retrieval, reflection) is enabled in the config."""
        return bool((self.cfg.get("agents") or {}).get(name, True))

    def run(self) -> Tree:
        """Run the whole search and return the finished tree.

        Prepares the task (unless resuming), adds nodes until a stopping rule fires, then
        chooses the final submission. A run that already finished is returned unchanged.

        If the LLM API fails, the half-made node is discarded and the controller waits and
        tries again; see outage(). After `llm.outage_retries` failures in a row it writes a
        checkpoint with stop_reason "llm_unavailable" and raises LLMUnavailable. The run is
        not finished, so `--resume` continues it.
        """
        if self.done:
            return self.tree
        if self.ctx is None:
            self.prepare()
            self.safe_point(current_node=None)

        failures = 0
        while (reason := self.stop_reason()) is None:
            started = time.monotonic()
            forced = self.state.forced_next
            operator, parent_id = self.select()
            try:
                node = self.run_node(operator, parent_id)
            except LLMUnavailable as e:
                failures += 1
                self.state.forced_next = forced  # a pending redirect is retried, not lost
                self.outage(e, failures, started)
                continue
            failures = 0
            if self.reflect is not None and self.agent_on("reflection"):
                try:
                    self.findings = self.reflect(self.llm, self.tree, self.findings, self.run_dir)
                except LLMUnavailable as e:  # findings stay as they were; A4 runs again after the next node
                    self.log_outage(e, failures=0, wait_s=0.0, during="reflection")
            self.safe_point(current_node=node.id)

        self.finalize(reason)
        return self.tree

    def outage(self, error: LLMUnavailable, failures: int, started: float) -> None:
        """Handle a failed LLM call during a node: discard the node, then wait or stop.

        Waits `llm.outage_wait_s`, doubling with each failure in a row, at most 5 minutes.
        The failed attempt and the wait are not charged to the budget, like the time between
        a crash and a resume. Raises the error once there have been `llm.outage_retries` failures.
        """
        llm_cfg = self.cfg.get("llm") or {}
        retries = llm_cfg.get("outage_retries", 5)
        for node_id in [n.id for n in self.tree.nodes.values() if n.status == NodeStatus.RUNNING]:
            del self.tree.nodes[node_id]  # never checkpointed, so nothing else refers to it
        self._set_aside_unfinished_nodes()

        if failures >= retries:
            self.log_outage(error, failures, wait_s=0.0, during="node")
            self._paused_s += time.monotonic() - started
            self.write_checkpoint(current_node=None, stop_reason="llm_unavailable", llm_error=str(error))
            raise error
        wait_s = min(llm_cfg.get("outage_wait_s", 30) * 2 ** (failures - 1), 300)
        self.log_outage(error, failures, wait_s, during="node")
        print(f"warning: LLM unavailable ({failures}/{retries}), retrying in {wait_s:.0f}s: {error}")
        self._sleep(wait_s)
        self._paused_s += time.monotonic() - started

    def log_outage(self, error: Exception, failures: int, wait_s: float, during: str) -> None:
        """Append one record to llm_errors.jsonl, for the cost analysis (wall clock lost to outages)."""
        record = {"timestamp": _now(), "during": during, "failures_in_a_row": failures,
                  "wait_s": wait_s, "error": str(error)}
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with (self.run_dir / "llm_errors.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def prepare(self) -> None:
        """Save the config, let A1 build the splits, and set up the shared workspace."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "config.yaml").write_text(yaml.safe_dump(self.cfg), encoding="utf-8")
        ctx = self.evaluator.prepare(self.task, self.run_dir, self.seed)

        self.workspace.mkdir(exist_ok=True)
        if Path(ctx.input_dir).resolve() != (self.workspace / "input").resolve():
            _link_tree(Path(ctx.input_dir), self.workspace / "input")
        self.ctx = SavedContext(
            description=ctx.description,
            input_dir=self.workspace / "input",
            prediction_format=ctx.prediction_format,
            metric=ctx.metric,
            higher_is_better=ctx.higher_is_better,
        )
        (self.run_dir / "task_context.json").write_text(self.ctx.model_dump_json(indent=2), encoding="utf-8")
        self.tree.higher_is_better = ctx.higher_is_better

    def select(self) -> tuple[Operator, str | None]:
        """The next (operator, parent id): a pending redirect if there is one, else the search policy."""
        forced, self.state.forced_next = self.state.forced_next, None
        if forced is not None:
            return Operator(forced["operator"]), forced["parent_id"]
        return select_next(self.tree, self.cfg["search"], self.rng)

    def cards(self) -> list[dict]:
        """Model cards for the prompt: A2's cards (unless A2 is off) plus any injected by monitors."""
        base = self.retrieved_cards() if self.agent_on("retrieval") else []
        return base + self.state.injected_cards

    def retrieved_cards(self) -> list[dict]:
        """A2's cards for this run, made once on first use (the first draft) and then reused.

        Web cards are saved in model_cards.json, so a resumed run gets the same cards
        without retrieving again. Without a retriever, the hand-written cards are used.
        """
        if self._cards is None:
            saved = self.run_dir / "model_cards.json"
            if saved.exists():
                self._cards = json.loads(saved.read_text(encoding="utf-8"))["cards"]
            elif self.retrieve is None:
                self._cards = retrieval.cards_for(self.task)
            else:
                self._cards = self.retrieve(self.llm, self.task, self.ctx, self.run_dir)
        return self._cards

    def generate(self, operator: Operator, parent: Node | None) -> tuple[str, str]:
        """Ask A3 for a plan and script for this operator. Raises CodingError on an unusable reply."""
        timeout_s = self.script_timeout_s()
        findings = self.findings if self.agent_on("reflection") else []
        if operator == Operator.DRAFT:
            previous = [n.plan for n in self.tree.nodes.values() if n.operator == Operator.DRAFT and n.plan]
            return coding.draft(
                self.llm, self.ctx, timeout_s, findings=findings, cards=self.cards(), previous_plans=previous
            )

        parent_dir = self.node_dir(parent.id)
        script = (self.run_dir / parent.script_path).read_text(encoding="utf-8")
        if operator == Operator.DEBUG:
            stderr_path = parent_dir / "stderr.txt"
            stderr = stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else ""
            error = parent.error or "unknown error"
            if stderr.strip() and "runtime_error" not in error:  # a runtime error already carries its stderr
                error += "\n\nEnd of stderr:\n" + coding.tail(stderr)
            return coding.debug(self.llm, self.ctx, timeout_s, script, error, findings=findings)

        stdout = parent_dir / "stdout.txt"
        output = stdout.read_text(encoding="utf-8") if stdout.exists() else ""
        return coding.improve(
            self.llm, self.ctx, timeout_s, script, parent.plan, parent.val_score, output,
            findings=findings, cards=self.cards(), tried=self.tried_improvements(parent),
            elsewhere=self.other_approaches(parent),
        )

    def tried_improvements(self, parent: Node) -> list[tuple[str, str]]:
        """(plan, outcome) for each finished improve attempt on `parent` that did not beat it.

        Successful attempts are left out: they are already better nodes, and the search
        moves to them.
        """
        tried = []
        min_gain = self.cfg["search"]["improve_min_rel_gain"]
        for child in self.tree.children(parent.id):
            if child.operator != Operator.IMPROVE or child.status == NodeStatus.RUNNING or not child.plan:
                continue
            if child.val_score is not None:
                if beats(self.tree, child.val_score, parent.val_score, min_gain):
                    continue
                outcome = f"validation {child.val_score:.4f}, not better"
            else:
                outcome = f"failed ({(child.error or 'unknown error').split(':')[0]})"
            tried.append((child.plan, outcome))
        return tried

    def other_approaches(self, parent: Node, limit: int = 12) -> list[tuple[str, str]]:
        """(plan, outcome) for drafts and improves on other branches, the `limit` most recent.

        Leaves out `parent` and its ancestors (the history of the script being improved),
        its own improve children (listed by tried_improvements), debug nodes (their plans
        describe fixes, not approaches) and nodes still running.
        """
        lineage, node = set(), parent
        while node is not None:
            lineage.add(node.id)
            node = self.tree.nodes.get(node.parent_id) if node.parent_id else None
        out = []
        for n in self.tree.nodes.values():
            if (n.id in lineage or n.parent_id == parent.id or n.operator == Operator.DEBUG
                    or n.status == NodeStatus.RUNNING or not n.plan):
                continue
            if n.val_score is not None:
                outcome = f"validation {n.val_score:.4f}"
            else:
                outcome = f"failed ({(n.error or 'unknown error').split(':')[0]})"
            out.append((n.plan, outcome))
        return out[-limit:]

    def run_node(self, operator: Operator, parent_id: str | None) -> Node:
        """Create one node: generate a script, screen it, execute it, score it, record the result.

        A failure at any stage gives a buggy node with a categorised error, not an exception.
        """
        node = Node(id=f"n{len(self.tree.nodes)}", parent_id=parent_id, operator=operator, started_at=_now())
        self.tree.add(node)
        node_dir = self.node_dir(node.id)
        output_dir = node_dir / "output"
        output_dir.mkdir(parents=True)
        parent = self.tree.nodes[parent_id] if parent_id else None

        try:
            node.plan, script = self.generate(operator, parent)
        except CodingError as e:
            return self._close(node, error=f"generation_error: {e}")
        (node_dir / "solution.py").write_text(script, encoding="utf-8")
        node.script_path = str(Path("nodes") / node.id / "solution.py")

        screen = getattr(self.evaluator, "screen", None)
        if screen is not None and self.agent_on("evaluation"):
            problem = screen(self.llm, script)
            if problem:
                return self._close(node, error=f"leakage: {problem}")

        exec_path = self.workspace / f"{node.id}.py"
        exec_path.write_text(coding.with_output_dir(script, self.sandbox.output_path(output_dir)), encoding="utf-8")
        # Recomputed: generating the script used some of the budget.
        timeout_s = self.script_timeout_s()
        result = self.sandbox.run(exec_path, self.workspace, output_dir, timeout_s)
        (node_dir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
        (node_dir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        if result.timed_out:
            return self._close(node, error=f"timeout: killed after {timeout_s:.0f}s")
        if result.exit_code != 0:
            return self._close(node, error=f"runtime_error: exit code {result.exit_code}\n{coding.tail(result.stderr)}")

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

    def _set_aside_unfinished_nodes(self) -> None:
        """Move folders of nodes that never reached a checkpoint to nodes/_unfinished, before reuse of their IDs."""
        nodes_root = self.run_dir / "nodes"
        if not nodes_root.exists():
            return
        for d in nodes_root.iterdir():
            if d.is_dir() and d.name.startswith("n") and d.name not in self.tree.nodes:
                stem = nodes_root / "_unfinished" / f"{d.name}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
                target, n = stem, 1
                while target.exists():  # the same ID set aside twice within a second
                    target, n = stem.with_name(f"{stem.name}_{n}"), n + 1
                target.parent.mkdir(exist_ok=True)
                d.rename(target)

    def _set_aside_incomplete_checkpoints(self, last_complete: int) -> None:
        """Rename checkpoint folders newer than `last_complete`, so monitors see the resumed run's checkpoints.

        A checkpoint cut short by a crash would otherwise stay the highest step, and
        checkpoint.read would keep returning nothing.
        """
        root = self.run_dir / "checkpoints"
        for d in root.iterdir():
            if d.is_dir() and d.name.isdigit() and int(d.name) > last_complete:
                d.rename(root / f"_incomplete_{d.name}")

    def write_checkpoint(self, current_node: str | None, **extra: Any) -> None:
        """Write a checkpoint of the tree, findings and run status. `extra` is added to status.json."""
        self.state.elapsed_s = round(self.elapsed_s(), 1)
        self.state.rng_state = _rng_state_to_json(self.rng.getstate())
        status = {
            "current_node": current_node,
            "elapsed_s": self.state.elapsed_s,
            "remaining_s": round(self.remaining_s(), 1),
            "timestamp": _now(),
            "task": self.task,
            "seed": self.seed,
            "condition": self.cfg.get("condition"),
            "done": False,
            **extra,
            "search": self.state.model_dump(mode="json"),
        }
        checkpoint.write(self.run_dir, self.state.step, self.tree.model_dump(mode="json"), self.findings, status)
        self.state.step += 1

    def safe_point(self, current_node: str | None) -> None:
        """Checkpoint, then apply queued interventions, then checkpoint again if any was applied."""
        self.write_checkpoint(current_node)
        records = apply_pending(self.run_dir, self.tree, self.findings, self.state)
        if any(r.outcome == "applied" for r in records):
            self.write_checkpoint(current_node)

    def choose_final(self) -> tuple[list[Node], str]:
        """The node(s) to submit, and how they were chosen.

        An applied override wins in every mode. Otherwise `final_selection` decides:
        best_val (and override with no override applied) takes the best node by validation
        score; top_k takes the best `top_k` (default 3).
        """
        best = ranked(self.tree)
        note = ""
        if self.state.override_node:
            node = self.tree.nodes.get(self.state.override_node)
            if node is not None and node.status == NodeStatus.WORKING:
                return [node], "override"
            note = "; override target no longer working"
        mode = self.cfg["final_selection"]
        if mode == "top_k":
            return best[: int(self.cfg.get("top_k", 3))], "top_k" + note
        if mode in ("best_val", "override"):
            return best[:1], "best_val" + note
        raise ValueError(f"unknown final_selection {mode!r}")

    def finalize(self, reason: str) -> None:
        """Apply late interventions, copy the chosen submission(s) into the run folder, write the last checkpoint.

        The first chosen node goes to submission.csv; with top_k every chosen node also goes
        to final/submission_<rank>.csv.
        """
        apply_pending(self.run_dir, self.tree, self.findings, self.state)
        chosen, how = self.choose_final()
        submitted = []
        for rank, node in enumerate(chosen, start=1):
            src = self.node_dir(node.id) / "submission.csv"
            if not src.exists():
                continue
            if not submitted:
                shutil.copyfile(src, self.run_dir / "submission.csv")
            if len(chosen) > 1:
                (self.run_dir / "final").mkdir(exist_ok=True)
                shutil.copyfile(src, self.run_dir / "final" / f"submission_{rank}.csv")
            submitted.append(node.id)
        self.done = True
        self.write_checkpoint(
            current_node=None,
            done=True,
            stop_reason=reason,
            final_selection=how,
            final_node=chosen[0].id if chosen else None,
            final_nodes=[n.id for n in chosen],
            submitted=bool(submitted),
        )


def main() -> None:
    """Command-line entry point: start a new run, or resume one, with the real sandbox, LLM and evaluator."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="condition file, for example configs/conditions/c1_autonomous.yaml")
    parser.add_argument("--task", help="MLE-bench competition ID")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--run-dir", help="default: runs/<condition>_<task>_seed<seed>_<utc time>")
    parser.add_argument("--resume", metavar="RUN_DIR", help="continue a run from its latest checkpoint")
    parser.add_argument("--sandbox", choices=["docker", "subprocess"], help="override sandbox.backend")
    args = parser.parse_args()
    load_dotenv()

    if args.resume:
        run_dir = Path(args.resume)
        cfg = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
        status = (latest_complete_checkpoint(run_dir) or {}).get("status", {})
        seed = status.get("seed", args.seed)
    else:
        if not (args.config and args.task):
            parser.error("--config and --task are required unless --resume is given")
        cfg = load_config(Path(args.config))
        seed = args.seed
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        default_name = f"{cfg.get('condition', 'run')}_{args.task}_seed{seed}_{stamp}"
        run_dir = Path(args.run_dir) if args.run_dir else Path("runs") / default_name

    from imle.agents import evaluation, reflection
    from imle.execution import make_sandbox
    from imle.llm import make_llm

    for name in ("prepare", "score"):
        if not hasattr(evaluation, name):
            raise SystemExit(
                f"imle.agents.evaluation.{name} is not implemented yet. "
                "Expected signature: docs/core-agent-assumptions.md"
            )
    reflect = getattr(reflection, "reflect", None)
    if reflect is None and (cfg.get("agents") or {}).get("reflection", True):
        print("warning: imle.agents.reflection.reflect is not implemented yet; running without findings")

    rcfg = cfg.get("retrieval") or {}
    retrieve = None
    if rcfg.get("source", "static") == "web":
        retrieve = retrieval.WebRetriever(Path(rcfg.get("cache_dir", "data/retrieval_cache")),
                                          max_cards=rcfg.get("max_cards", 8))

    deps = {
        "llm": make_llm(cfg, run_dir, seed),
        "sandbox": make_sandbox(cfg, args.sandbox),
        "evaluator": evaluation,
        "reflect": reflect,
        "retrieve": retrieve,
    }
    if args.resume:
        controller = Controller.resume(run_dir, **deps)
    else:
        controller = Controller(cfg, args.task, seed, run_dir, **deps)
    try:
        controller.run()
    except LLMUnavailable as e:
        raise SystemExit(f"stopped, the LLM API is unavailable ({e}). Continue later with: "
                         f"python -m imle.controller --resume {run_dir}") from e
    print(f"run finished: {run_dir}")


if __name__ == "__main__":
    main()
