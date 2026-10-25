"""Findings: what A4 concludes from the tree, with the evidence it rests on.

Stored in checkpoints as plain dicts (`checkpoint.write(findings=...)`), so the
controller, `apply._correct`, the dashboard and `coding.render_findings` work on
them without importing this module. The dict form is a superset of the one in
docs/core-agent-assumptions.md:

    {"id": "f-3a9c...", "text": "...", "step": 7, "effect": "helps",
     "evidence": [{"node_id": "n3", "val_score": 0.41, "probe_score": 0.43}]}

`effect` says what the cited nodes are claimed to show (see scripts/finding_accuracy.py),
so whether a finding is supported can be checked from the scores alone.
"""

from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Effect(str, Enum):
    HELPS = "helps"      # the cited nodes did better than their parents on validation
    HURTS = "hurts"      # the cited nodes did worse than their parents, or crashed
    NEUTRAL = "neutral"  # an observation with no direction, such as a runtime limit


class Evidence(BaseModel):
    node_id: str
    val_score: float | None = None
    probe_score: float | None = None   # filled by code for monitors; never shown to the agent


class Finding(BaseModel):
    id: str
    text: str
    step: int = 0                      # finished nodes when the finding was written
    effect: Effect = Effect.NEUTRAL
    evidence: list[Evidence] = Field(default_factory=list)

    @classmethod
    def create(cls, text: str, evidence: list[Evidence], step: int = 0,
               effect: Effect | str = Effect.NEUTRAL) -> Finding:
        """A finding with its content-based ID."""
        return cls(id=finding_id(text, [e.node_id for e in evidence]), text=text.strip(), step=step,
                   effect=Effect(effect), evidence=evidence)

    def to_dict(self) -> dict[str, Any]:
        """The JSON form stored in findings.json."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        """Read a stored finding, including the older form without `step` and `effect`."""
        return cls.model_validate(data)


def normalise(text: str) -> str:
    """Lower case, punctuation removed, whitespace collapsed: two wordings that differ only in these are one finding."""
    return " ".join(re.sub(r"[^\w\s.]", " ", text.lower()).split()).strip(" .")


def finding_id(text: str, node_ids: list[str]) -> str:
    """A stable ID from the normalised text and the cited nodes, independent of their order."""
    key = normalise(text) + "|" + ",".join(sorted(set(node_ids)))
    return "f-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]
