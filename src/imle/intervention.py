"""Intervention schema and queue. Shared contract: change by PR only.

See docs/intervention-protocol.md.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Action(str, Enum):
    PRUNE = "prune"
    REDIRECT = "redirect"
    OVERRIDE = "override"
    INJECT = "inject"
    CORRECT = "correct"
    REBUDGET = "rebudget"
    ABANDON = "abandon"


ACTION_KIND = {
    Action.PRUNE: "action",
    Action.REDIRECT: "action",
    Action.OVERRIDE: "action",
    Action.INJECT: "belief",
    Action.CORRECT: "belief",
    Action.REBUDGET: "budget",
    Action.ABANDON: "budget",
}


class Intervention(BaseModel):
    id: str
    ts: str
    source: str                      # "human" or a policy name
    action: Action
    target: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None


class AppliedRecord(BaseModel):
    intervention: Intervention
    outcome: str                     # "applied" or "dropped"
    reason: str | None = None
    applied_at: str


def append(queue_path: Path, item: Intervention) -> None:
    """Monitors call this. Append-only, one JSON object per line."""
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        f.write(item.model_dump_json() + "\n")


def read_all(queue_path: Path) -> list[Intervention]:
    """Every valid queue item, in timestamp order.

    A malformed line (bad JSON, unknown action, missing field) is reported and skipped, so
    one bad write by a monitor cannot block the items after it.
    """
    if not queue_path.exists():
        return []
    items = []
    for number, line in enumerate(queue_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            items.append(Intervention.model_validate(json.loads(line)))
        except ValueError as e:  # json.JSONDecodeError and pydantic's ValidationError are both ValueErrors
            print(f"warning: {queue_path.name} line {number} skipped: {str(e).splitlines()[0]}")
    return sorted(items, key=lambda i: i.ts)


def pending(queue_path: Path, applied_path: Path) -> list[Intervention]:
    """Queue items not yet applied or dropped. Called by the controller at a safe point."""
    done = set()
    if applied_path.exists():
        for line in applied_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["intervention"]["id"])
    return [i for i in read_all(queue_path) if i.id not in done]
