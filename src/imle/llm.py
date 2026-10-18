"""LLM client: one prompt in, completion text out, every call logged.

Calls Claude through the Anthropic SDK. Each call is logged with role 1's
`imle.llm_log.log_llm_call` when that function exists, and otherwise with an
identical record written here, to runs/<run_id>/llm_calls.jsonl.

Current Claude models reject sampling parameters, so `llm.temperature` in the
config is not sent. Reasoning depth is set with `llm.effort` instead.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from imle.llm_log import log_llm_call
except ImportError:  # role 1's logger not merged yet
    log_llm_call = None

DEFAULT_MODEL = "claude-opus-5-5"

# Models that accept server-side refusal fallbacks (`fallbacks: "default"`).
FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"

# USD per million input and output tokens, for the cost column of the log.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


class AnthropicLLM:
    """Callable as `llm(agent=..., system=..., user=...) -> str`, the interface the agents use."""

    def __init__(
        self,
        model: str | None,
        run_dir: Path,
        *,
        effort: str = "high",
        max_tokens: int = 64000,
        seed: int | None = None,
        client: Any = None,
    ) -> None:
        """`model` falls back to DEFAULT_MODEL when it is empty or an unexpanded ${VAR}."""
        self.model = model if model and "${" not in model else DEFAULT_MODEL
        self.run_dir = Path(run_dir)
        self.effort = effort
        self.max_tokens = max_tokens
        self.seed = seed
        self._client = client

    def client(self) -> Any:
        """The Anthropic client, created on first use so tests and imports need no credentials."""
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(max_retries=5)
        return self._client

    def request_args(self, system: str, user: str) -> dict[str, Any]:
        """Keyword arguments for one Messages API request."""
        args: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"effort": self.effort},
        }
        if self.model in FALLBACK_MODELS:
            args["betas"] = [FALLBACK_BETA]
            args["fallbacks"] = "default"
        return args

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        """Send one prompt, log the call, and return the text of the reply.

        Streams the response so long replies do not hit the HTTP timeout. A refused or
        truncated reply is returned as is; the caller sees it as a reply with no script.
        """
        args = self.request_args(system, user)
        start = time.monotonic()
        with self.client().beta.messages.stream(**args) as stream:
            message = stream.get_final_message()
        latency_s = time.monotonic() - start

        text = "".join(block.text for block in message.content if block.type == "text")
        sampling = {k: args[k] for k in ("max_tokens", "output_config", "fallbacks") if k in args}
        sampling["stop_reason"] = message.stop_reason
        self._log(agent, system, user, text, message.model, message.usage, latency_s, sampling)
        return text

    def _log(self, agent, system, user, text, model, usage, latency_s, sampling) -> None:
        """Write one llm_calls.jsonl record, through role 1's logger when it is available."""
        record = {
            "run_id": self.run_dir.name,
            "agent": agent,
            "model": model,
            "prompt": f"### SYSTEM\n{system}\n\n### USER\n{user}",
            "completion": text,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "latency_s": round(latency_s, 3),
            "seed": self.seed,
            "sampling_params": sampling,
            "cost_usd": cost_usd(model, usage.input_tokens, usage.output_tokens),
        }
        if log_llm_call is not None:
            log_llm_call(**record, runs_dir=self.run_dir.parent)
            return
        path = self.run_dir / "llm_calls.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}) + "\n")


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """API cost of one call in US dollars, or None for a model without a known price."""
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)
