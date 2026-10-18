"""Search state that is not part of the tree.

Written into status.json at every safe point, so a crashed run resumes with the
same budget, random state and pending intervention effects.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchState(BaseModel):
    """Everything the controller needs, besides the tree and findings, to continue a run."""

    step: int = 0                                 # index of the next checkpoint
    elapsed_s: float = 0.0                        # budget used up to the last checkpoint
    extra_budget_s: float = 0.0                   # added (or removed) by `rebudget`
    override_node: str | None = None              # set by `override`
    forced_next: dict[str, Any] | None = None     # set by `redirect`: {"operator", "parent_id"}
    injected_cards: list[dict[str, Any]] = Field(default_factory=list)  # added by `inject`
    rng_state: list[Any] | None = None
