"""Search tree data model. Shared contract: change by PR only.

Each node is one self-contained script plus its scores. The tree is written only
by the controller (A5).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Operator(str, Enum):
    DRAFT = "draft"
    DEBUG = "debug"
    IMPROVE = "improve"


class NodeStatus(str, Enum):
    RUNNING = "running"
    WORKING = "working"      # executed and scored
    BUGGY = "buggy"          # raised an error or produced an invalid submission
    ABANDONED = "abandoned"  # terminated by an `abandon` intervention; no score
    PRUNED = "pruned"        # excluded from selection by a `prune` intervention


class Node(BaseModel):
    id: str
    parent_id: Optional[str] = None
    operator: Operator
    plan: str = ""
    script_path: str = ""
    status: NodeStatus = NodeStatus.RUNNING
    val_score: Optional[float] = None
    probe_score: Optional[float] = None   # hidden from the agent, shown to monitors
    test_score: Optional[float] = None    # graded for analysis, never shown to any agent
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class Tree(BaseModel):
    nodes: dict[str, Node] = Field(default_factory=dict)
    higher_is_better: bool = True

    def add(self, node: Node) -> None:
        if node.id in self.nodes:
            raise ValueError(f"duplicate node id {node.id}")
        if node.parent_id is not None and node.parent_id not in self.nodes:
            raise ValueError(f"unknown parent {node.parent_id}")
        self.nodes[node.id] = node

    def children(self, node_id: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.parent_id == node_id]

    def subtree_ids(self, node_id: str) -> list[str]:
        out, stack = [], [node_id]
        while stack:
            cur = stack.pop()
            out.append(cur)
            stack.extend(c.id for c in self.children(cur))
        return out

    def selectable(self) -> list[Node]:
        return [n for n in self.nodes.values() if n.status == NodeStatus.WORKING]

    def best_by_val(self) -> Optional[Node]:
        cands = [n for n in self.selectable() if n.val_score is not None]
        if not cands:
            return None
        key = (lambda n: n.val_score) if self.higher_is_better else (lambda n: -n.val_score)
        return max(cands, key=key)
