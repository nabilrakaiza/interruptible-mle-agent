"""A4: reflection agent.

At phase boundaries, compresses completed nodes into findings. Every finding
carries its evidence (node IDs and scores) so it can be checked or corrected.

The controller calls `reflect` after every node (docs/core-agent-assumptions.md).
It acts only at a phase boundary: once the first `search.num_drafts` nodes have
finished, then every `reflection.every_n` finished nodes (default 10). The next
boundary is kept in <run_dir>/a4/state.json, so a resumed run or an LLM outage
picks up where it stopped.

A4 reads only the tree: each node's plan, operator, status, error category and
validation score. It never sees data, and never sees probe or test scores, because
its findings go into A3's prompt. Code, not the model, copies each cited node's
validation and probe scores into the finding's evidence, for monitors and C5.

This module also holds `ask_json`, the structured-output loop shared with A1's
optional LLM leakage review.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel, Field, ValidationError

from imle.agents.coding import LLM
from imle.findings import Effect, Evidence, Finding, normalise
from imle.tree import Node, NodeStatus, Tree

M = TypeVar("M", bound=BaseModel)

MAX_RETRIES = 2

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class StructuredOutputError(Exception):
    """The model did not return valid JSON for the schema within the allowed attempts."""


def parse_json(text: str) -> object:
    """The JSON value in a reply, allowing a ```json fence or text around one object."""
    text = text.strip()
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def ask_json(llm: LLM, *, agent: str, system: str, user: str, schema: type[M], max_retries: int = MAX_RETRIES,
             check=None) -> M:
    """Ask for JSON matching `schema`, retrying up to `max_retries` times with the error shown.

    `check(model)` may raise ValueError for problems the schema cannot express, such
    as unknown node IDs; that counts as an invalid reply too. LLMUnavailable from the
    client is not caught. Raises StructuredOutputError after the last attempt.
    """
    prompt, errors = user, []
    for _ in range(max_retries + 1):
        reply = llm(agent=agent, system=system, user=prompt)
        try:
            model = schema.model_validate(parse_json(reply))
            if check is not None:
                check(model)
            return model
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            error = str(e).splitlines()[0] if isinstance(e, json.JSONDecodeError) else str(e)
            errors.append(error[:300])
            prompt = (f"{user}\n\nYour previous reply was not valid: {error[:300]}\n"
                      "Reply again with only the JSON object, in the format given above.")
    raise StructuredOutputError(f"{agent}: no valid JSON after {max_retries + 1} attempts: {errors[-1]}")


# --------------------------------------------------------------------------- reflection

A4_DIR = "a4"
EVERY_N = 10
MAX_FINDINGS = 10
NEW_PER_CALL = 3
PLAN_CHARS = 240

SYSTEM = ("You review the progress of an automated machine learning search and record short, reusable lessons. "
          "You answer with one JSON object only.")

PROMPT = """\
An agent is solving a machine learning task by writing scripts. Each node below is
one script: a draft (new solution), an improve of a working node, or a debug of a
buggy node. The metric is {metric} ({direction} is better).

# Nodes

{nodes}

# Findings already recorded

{existing}

# Instructions

Write up to {k} new findings that are not already recorded: lessons that would help
write the next scripts, such as which approaches or changes helped or hurt on
validation, and which errors to avoid. Each finding is one or two sentences and must
cite the node IDs that show it. Set "effect" to "helps" if the cited nodes scored
better than their parents on validation, "hurts" if they scored worse or crashed,
and "neutral" otherwise. If there is nothing new, return an empty list.

Answer with exactly this JSON object:
{{"findings": [{{"text": "...", "effect": "helps" | "hurts" | "neutral", "evidence": ["n3", "n7"]}}]}}"""


class ReflectionError(Exception):
    """A4 could not produce valid findings."""


class ProposedFinding(BaseModel):
    text: str = Field(min_length=10, max_length=400)
    effect: Effect
    evidence: list[str] = Field(min_length=1, max_length=10)


class ReflectionReply(BaseModel):
    findings: list[ProposedFinding] = Field(max_length=NEW_PER_CALL)


def _settings(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "config.yaml"
    cfg = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.exists() else {}
    a4 = cfg.get("reflection") or {}
    return {"num_drafts": int((cfg.get("search") or {}).get("num_drafts", 5)),
            "every_n": int(a4.get("every_n", EVERY_N)),
            "max_findings": int(a4.get("max_findings", MAX_FINDINGS)),
            "max_retries": int(a4.get("max_retries", MAX_RETRIES))}


def _finished(tree: Tree) -> list[Node]:
    return [n for n in tree.nodes.values() if n.status != NodeStatus.RUNNING]


def describe_node(node: Node) -> str:
    """One line per node for the prompt: validation score only, never probe or test."""
    origin = node.operator.value if node.parent_id is None else f"{node.operator.value} of {node.parent_id}"
    if node.status == NodeStatus.WORKING and node.val_score is not None:
        outcome = f"working, validation {node.val_score:.5g}"
    elif node.status == NodeStatus.BUGGY:
        outcome = f"buggy ({(node.error or 'error').split(':', 1)[0]})"
    else:
        outcome = node.status.value
    plan = " ".join(node.plan.split())[:PLAN_CHARS]
    return f"- {node.id} ({origin}): {outcome}. Plan: {plan}"


def describe_finding(f: dict[str, Any]) -> str:
    cited = ", ".join(e.get("node_id", "?") for e in f.get("evidence", []) if isinstance(e, dict))
    return f"- [{f.get('id')}] {f.get('text', '')} ({f.get('effect', 'neutral')}; evidence {cited or 'none'})"


def reflection_prompt(tree: Tree, findings: list[dict[str, Any]], metric: str, k: int = NEW_PER_CALL) -> str:
    nodes = sorted(_finished(tree), key=lambda n: int(n.id[1:]) if n.id[1:].isdigit() else n.id)
    return PROMPT.format(metric=metric, direction="higher" if tree.higher_is_better else "lower",
                         nodes="\n".join(describe_node(n) for n in nodes),
                         existing="\n".join(describe_finding(f) for f in findings) or "None yet.", k=k)


def propose(llm: LLM, tree: Tree, findings: list[dict[str, Any]], step: int, metric: str = "the task metric",
            max_retries: int = MAX_RETRIES) -> list[Finding]:
    """Ask A4 for new findings about the finished nodes. Raises ReflectionError if no valid reply arrives."""
    finished = {n.id for n in _finished(tree)}

    def check(reply: ReflectionReply) -> None:
        unknown = sorted({i for f in reply.findings for i in f.evidence} - finished)
        if unknown:
            raise ValueError(f"unknown or unfinished node IDs cited: {unknown}")

    try:
        reply = ask_json(llm, agent="reflection", system=SYSTEM, user=reflection_prompt(tree, findings, metric),
                         schema=ReflectionReply, max_retries=max_retries, check=check)
    except StructuredOutputError as e:
        raise ReflectionError(str(e)) from e
    out = []
    for p in reply.findings:
        evidence = [Evidence(node_id=i, val_score=tree.nodes[i].val_score, probe_score=tree.nodes[i].probe_score)
                    for i in dict.fromkeys(p.evidence)]
        out.append(Finding.create(p.text, evidence, step=step, effect=p.effect))
    return out


def merge(findings: list[dict[str, Any]], new: list[Finding], max_findings: int = MAX_FINDINGS) -> list[dict[str, Any]]:
    """Existing findings plus the new ones that are not duplicates, keeping the newest `max_findings`."""
    seen_ids = {f.get("id") for f in findings}
    seen_text = {normalise(str(f.get("text", ""))) for f in findings}
    out = list(findings)
    for f in new:
        if f.id in seen_ids or normalise(f.text) in seen_text:
            continue
        out.append(f.to_dict())
        seen_ids.add(f.id)
        seen_text.add(normalise(f.text))
    return out[-max_findings:] if max_findings > 0 else out


def _state(run_dir: Path, first: int) -> dict[str, int]:
    path = run_dir / A4_DIR / "state.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"next_boundary": first}


def _save_state(run_dir: Path, state: dict[str, int]) -> None:
    path = run_dir / A4_DIR / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def reflect(llm: LLM, tree: Tree, findings: list[dict[str, Any]], run_dir: Path) -> list[dict[str, Any]]:
    """The controller's hook: the findings after the latest node, updated only at a phase boundary.

    LLMUnavailable propagates (the controller retries after the next node, and the
    boundary stays pending). An invalid reply after all retries is logged to
    a4/errors.jsonl with a warning, the findings stay unchanged, and A4 waits for
    the next boundary rather than retrying after every node.
    """
    run_dir = Path(run_dir)
    settings = _settings(run_dir)
    state = _state(run_dir, settings["num_drafts"])
    finished = len(_finished(tree))
    if finished < state["next_boundary"]:
        return findings

    context = run_dir / "task_context.json"
    metric = json.loads(context.read_text(encoding="utf-8")).get("metric", "the task metric") \
        if context.exists() else "the task metric"
    try:
        new = propose(llm, tree, findings, step=finished, metric=metric, max_retries=settings["max_retries"])
        result = merge(findings, new, settings["max_findings"])
    except ReflectionError as e:
        print(f"warning: A4 reflection failed at {finished} nodes, findings unchanged: {e}")
        log = run_dir / A4_DIR / "errors.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "finished_nodes": finished,
                                "error": str(e)}) + "\n")
        result = findings
    _save_state(run_dir, {"next_boundary": finished + settings["every_n"]})
    return result
