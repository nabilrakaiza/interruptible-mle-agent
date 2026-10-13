"""Structured logging for every LLM call and every execution.

Each LLM call records: agent, prompt, completion, model version string,
sampling parameters, input/output tokens, latency, timestamp, seed.
Written to runs/<run_id>/llm_calls.jsonl.
"""

"""Structured JSONL logging for LLM calls and experiment executions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append one JSON record to a log file."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_llm_call(
    run_id: str,
    agent: str,
    model: str,
    prompt: str,
    completion: str,
    input_tokens: int,
    output_tokens: int,
    latency_s: float,
    seed: int | None = None,
    sampling_params: dict | None = None,
    cost_usd: float | None = None,
    runs_dir: str | Path = "runs",
) -> None:
    """Record one LLM API call."""

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "agent": agent,
        "model": model,
        "prompt": prompt,
        "completion": completion,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_s": latency_s,
        "seed": seed,
        "sampling_params": sampling_params or {},
        "cost_usd": cost_usd,
    }

    log_path = Path(runs_dir) / run_id / "llm_calls.jsonl"
    append_jsonl(log_path, record)
