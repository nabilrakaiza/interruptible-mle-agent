"""A3: coding agent.

Operators: draft, debug, improve. Output: a short plan plus a self-contained
script that trains, scores itself through the frozen harness, and writes a
submission. No network access, no write access to the harness.

Only draft is implemented so far. The script contract (what the script reads
and writes) is described in docs/core-agent-assumptions.md.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

# Packages the prompt tells the model it may import. Must match the sandbox image.
PACKAGES = "numpy, pandas, scipy, scikit-learn"

SYSTEM = (
    "You are an expert machine learning engineer working on a Kaggle-style competition. "
    "Each reply contains a short plan and one complete, self-contained Python script."
)

RESPONSE_FORMAT = """\
Reply in exactly this format and nothing else:

PLAN: three to five sentences describing the approach.

```python
# the complete script
```"""

_CODE_BLOCK = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


class LLM(Protocol):
    """The LLM wrapper, llm_log.complete, with model settings already bound. Implemented by role 1."""

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        """Send one system and user prompt to the model and return the completion text.

        `agent` names the caller in llm_calls.jsonl. The call is logged by the wrapper.
        """
        ...


class TaskContext(Protocol):
    """What A1 hands over after building the splits. See evaluation.prepare."""

    description: str            # competition description, as given to a human competitor
    input_dir: Path             # visible to the script as ./input
    prediction_format: str      # what predictions.csv must contain
    metric: str
    higher_is_better: bool


class CodingError(Exception):
    """The model did not return a usable script."""


def describe_inputs(input_dir: Path, max_entries: int = 30, max_line: int = 300) -> str:
    """List the input files, with the first rows of each CSV, for the prompt."""
    lines = []
    entries = sorted(input_dir.iterdir())
    for p in entries[:max_entries]:
        if p.is_dir():
            names = sorted(c.name for c in p.iterdir())
            lines.append(f"- input/{p.name}/ ({len(names)} entries, e.g. {', '.join(names[:3])})")
            continue
        lines.append(f"- input/{p.name} ({p.stat().st_size:,} bytes)")
        if p.suffix == ".csv":
            with p.open(encoding="utf-8", errors="replace") as f:
                for _ in range(4):
                    row = f.readline().rstrip("\n")
                    if not row:
                        break
                    lines.append("    " + (row if len(row) <= max_line else row[:max_line] + " ..."))
    if len(entries) > max_entries:
        lines.append(f"- ... and {len(entries) - max_entries} more")
    return "\n".join(lines)


def draft_prompt(ctx: TaskContext, timeout_s: float) -> str:
    """The user prompt for a draft: task, data preview, output contract and constraints."""
    direction = "higher" if ctx.higher_is_better else "lower"
    return f"""\
# Task

{ctx.description.strip()}

# Data

The script runs in an empty working directory. The inputs are read-only, under ./input:

{describe_inputs(ctx.input_dir)}

input/train.csv is labelled. Use it for fitting, and hold part of it out yourself if you
want to check your model. input/predict.csv is unlabelled and you must predict every row.

# Output

Write ./predictions.csv. {ctx.prediction_format.strip()}

Predictions are scored outside the script with {ctx.metric} ({direction} is better).
The labels for predict.csv are not available to you.

# Constraints

- One self-contained script. No network access and no user input.
- CPU only. The script is killed after {int(timeout_s)} seconds, so stay well under that.
- Available packages: {PACKAGES}.
- Write only inside the working directory.

# Instructions

Write a first solution. Prefer a simple approach that is certain to run and finish
over an ambitious one.

{RESPONSE_FORMAT}"""


def parse_response(text: str) -> tuple[str, str]:
    """Split a reply into (plan, script). Raises CodingError if there is no script."""
    m = _CODE_BLOCK.search(text)
    if m is None or not m.group(1).strip():
        raise CodingError("reply has no complete python code block")
    plan = text[: m.start()].strip()
    plan = re.sub(r"^PLAN:\s*", "", plan, flags=re.IGNORECASE)
    return plan, m.group(1)


def _generate(llm: LLM, prompt: str, attempts: int = 2) -> tuple[str, str]:
    """Call the model and parse the reply, asking again if a reply has no script."""
    for _ in range(attempts - 1):
        try:
            return parse_response(llm(agent="coding", system=SYSTEM, user=prompt))
        except CodingError:
            pass
    return parse_response(llm(agent="coding", system=SYSTEM, user=prompt))


def draft(llm: LLM, ctx: TaskContext, timeout_s: float) -> tuple[str, str]:
    """A new solution from scratch. Returns (plan, script)."""
    return _generate(llm, draft_prompt(ctx, timeout_s))
