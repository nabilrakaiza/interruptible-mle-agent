"""A5: tree controller and main loop.

Responsibilities:
    - select the next node and operator (greedy on validation score to start)
    - enforce stopping rules (budget, node cap, debug depth, improve stagnation)
    - checkpoint at every safe point
    - drain the intervention queue and apply or drop each action
    - choose the final submission (best-val, top-k, or human override)

The controller is the ONLY writer to the tree.
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    raise NotImplementedError("Controller loop not implemented yet. See docs/architecture.md.")


if __name__ == "__main__":
    main()
