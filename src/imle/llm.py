"""LLM clients: one prompt in, completion text out, every call logged.

Providers, chosen by `llm.provider` in the config:

    openrouter  (default) any OpenRouter model, through its OpenAI-compatible API.
                Needs OPENROUTER_API_KEY. Default model xiaomi/mimo-v2.6-flash.
    gemini      Gemini through Google's OpenAI-compatible endpoint, for cheap local
                testing. Needs GEMINI_API_KEY. Default model gemini-3.5-flash-lite.

Each call is logged with role 1's `imle.llm_log.log_llm_call` when that function
exists, and otherwise with an identical record written here, to
runs/<run_id>/llm_calls.jsonl.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from imle.llm_log import log_llm_call
except ImportError:  # role 1's logger not merged yet
    log_llm_call = None

# Providers reached through the OpenAI-compatible chat completions API. `effort_as` says how
# reasoning effort is sent: OpenRouter's `reasoning` object, or the standard `reasoning_effort`.
# `sends_seed` is False where the API rejects the field (Gemini answers 400 "Unknown name seed").
OPENAI_COMPATIBLE = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "effort_as": "reasoning",
        "sends_seed": True,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "effort_as": "reasoning_effort",
        "sends_seed": False,
    },
}
DEFAULT_MODELS = {
    "openrouter": "xiaomi/mimo-v2.6-flash",
    "gemini": "gemini-3.5-flash-lite",
}

# USD per million input and output tokens, used when the provider does not report a cost.
PRICES = {
    "xiaomi/mimo-v2.6-flash": (0.14, 0.28),
}


def _model_or_default(model: str | None, provider: str) -> str:
    """`model`, or the provider's default when it is empty or an unexpanded ${VAR}."""
    return model if model and "${" not in model else DEFAULT_MODELS[provider]


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """API cost of one call in US dollars, or None for a model without a known price."""
    if model not in PRICES:
        return None
    price_in, price_out = PRICES[model]
    return round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 6)


def write_log(run_dir: Path, seed: int | None, agent: str, system: str, user: str, completion: str,
              model: str, input_tokens: int, output_tokens: int, latency_s: float,
              sampling: dict[str, Any], cost: float | None) -> None:
    """Write one llm_calls.jsonl record, through role 1's logger when it is available."""
    record = {
        "run_id": run_dir.name,
        "agent": agent,
        "model": model,
        "prompt": f"### SYSTEM\n{system}\n\n### USER\n{user}",
        "completion": completion,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_s": round(latency_s, 3),
        "seed": seed,
        "sampling_params": sampling,
        "cost_usd": cost,
    }
    if log_llm_call is not None:
        log_llm_call(**record, runs_dir=run_dir.parent)
        return
    path = run_dir / "llm_calls.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **record}) + "\n")


class OpenAICompatibleLLM:
    """Callable as `llm(agent=..., system=..., user=...) -> str`, served through a chat completions API."""

    def __init__(
        self,
        model: str | None,
        run_dir: Path,
        *,
        provider: str = "openrouter",
        temperature: float | None = 0.7,
        effort: str | None = "high",
        max_tokens: int = 64000,
        seed: int | None = None,
        client: Any = None,
    ) -> None:
        """`provider` is a key of OPENAI_COMPATIBLE. `effort` (low, medium or high) sets reasoning depth;
        None leaves the model's default.
        """
        self.provider = provider
        self.settings = OPENAI_COMPATIBLE[provider]
        self.model = _model_or_default(model, provider)
        self.run_dir = Path(run_dir)
        self.temperature = temperature
        self.effort = effort
        self.max_tokens = max_tokens
        self.seed = seed
        self._client = client

    def client(self) -> Any:
        """The OpenAI-compatible client pointed at the provider, created on first use."""
        if self._client is None:
            from openai import OpenAI

            key = os.environ.get(self.settings["key_env"])
            if not key:
                raise RuntimeError(f"{self.settings['key_env']} is not set; put it in .env")
            self._client = OpenAI(base_url=self.settings["base_url"], api_key=key, max_retries=5, timeout=900)
        return self._client

    def request_args(self, system: str, user: str) -> dict[str, Any]:
        """Keyword arguments for one chat completion request."""
        args: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            args["temperature"] = self.temperature
        if self.seed is not None and self.settings["sends_seed"]:
            args["seed"] = self.seed
        if self.effort in ("low", "medium", "high"):
            if self.settings["effort_as"] == "reasoning":
                args["extra_body"] = {"reasoning": {"effort": self.effort}}
            else:
                args["reasoning_effort"] = self.effort
        return args

    def __call__(self, *, agent: str, system: str, user: str) -> str:
        """Send one prompt, log the call, and return the text of the reply.

        Reasoning text is not returned or logged, only the answer. A truncated or empty
        reply is returned as is; the caller sees it as a reply with no script.
        """
        args = self.request_args(system, user)
        start = time.monotonic()
        response = self.client().chat.completions.create(**args)
        latency_s = time.monotonic() - start

        choice = response.choices[0]
        text = choice.message.content or ""
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        reported = getattr(usage, "cost", None)
        cost = float(reported) if reported is not None else cost_usd(self.model, input_tokens, output_tokens)
        sampling = {k: v for k, v in args.items() if k not in ("model", "messages")}
        sampling["finish_reason"] = choice.finish_reason
        write_log(self.run_dir, self.seed, agent, system, user, text, response.model or self.model,
                  input_tokens, output_tokens, latency_s, sampling, cost)
        return text


def make_llm(cfg: dict, run_dir: Path, seed: int | None) -> OpenAICompatibleLLM:
    """The client named by `llm.provider` (default openrouter), configured from the `llm` section."""
    llm_cfg = cfg.get("llm") or {}
    provider = llm_cfg.get("provider", "openrouter")
    if provider not in OPENAI_COMPATIBLE:
        raise ValueError(f"unknown llm.provider {provider!r}")
    return OpenAICompatibleLLM(
        llm_cfg.get("model"),
        run_dir,
        provider=provider,
        temperature=llm_cfg.get("temperature"),
        effort=llm_cfg.get("effort", "high"),
        max_tokens=int(llm_cfg.get("max_tokens", 64000)),
        seed=seed,
    )
