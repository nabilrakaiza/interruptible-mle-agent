"""Atomic checkpoint read/write. Shared contract: change by PR only.

The agent writes; monitors read. Writes go to a temp file and are renamed, so a
reader never sees a partially written file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def checkpoint_dir(run_dir: Path, step: int) -> Path:
    return run_dir / "checkpoints" / f"{step:06d}"


def latest_step(run_dir: Path) -> int | None:
    root = run_dir / "checkpoints"
    if not root.exists():
        return None
    steps = [int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit()]
    return max(steps) if steps else None


def write(run_dir: Path, step: int, tree: dict, findings: list, status: dict) -> None:
    d = checkpoint_dir(run_dir, step)
    atomic_write_json(d / "tree.json", tree)
    atomic_write_json(d / "findings.json", findings)
    # status last: its presence marks the checkpoint as complete
    atomic_write_json(d / "status.json", status)


def read(run_dir: Path, step: int | None = None) -> dict | None:
    step = latest_step(run_dir) if step is None else step
    if step is None:
        return None
    d = checkpoint_dir(run_dir, step)
    if not (d / "status.json").exists():
        return None  # incomplete checkpoint
    return {
        "step": step,
        "tree": json.loads((d / "tree.json").read_text()),
        "findings": json.loads((d / "findings.json").read_text()),
        "status": json.loads((d / "status.json").read_text()),
    }
