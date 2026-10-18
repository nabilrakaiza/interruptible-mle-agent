import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from imle import llm as llm_module
from imle.llm import OpenAICompatibleLLM, cost_usd, make_llm

REPLY = "PLAN: x\n```python\npass\n```"


class FakeOpenRouter:
    """Records each chat.completions.create call and returns a fixed completion."""

    def __init__(self, content: str | None = REPLY, cost: float | None = 0.0005):
        """Every call returns `content`, with `cost` reported in usage when it is not None."""
        self.calls = []
        usage = SimpleNamespace(prompt_tokens=1000, completion_tokens=500)
        if cost is not None:
            usage.cost = cost
        response = SimpleNamespace(
            model="xiaomi/mimo-v2.6-flash",
            choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
            usage=usage,
        )

        def create(**kwargs):
            """Record the request and return the fixed response."""
            self.calls.append(kwargs)
            return response

        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))


def read_log(run_dir: Path) -> dict:
    """The first record of a run's llm_calls.jsonl."""
    return json.loads((run_dir / "llm_calls.jsonl").read_text().splitlines()[0])


def test_openrouter_request_and_log(tmp_path: Path, monkeypatch):
    """One OpenRouter call sends temperature, seed and reasoning effort, and logs the reported cost."""
    monkeypatch.setattr(llm_module, "log_llm_call", None)
    client = FakeOpenRouter()
    llm = OpenAICompatibleLLM("${LLM_MODEL}", tmp_path / "run1", temperature=0.7, effort="high", seed=3, client=client)
    assert llm(agent="coding", system="sys", user="hello") == REPLY

    sent = client.calls[0]
    assert sent["model"] == "xiaomi/mimo-v2.6-flash"
    assert sent["messages"] == [{"role": "system", "content": "sys"}, {"role": "user", "content": "hello"}]
    assert sent["temperature"] == 0.7 and sent["seed"] == 3
    assert sent["extra_body"] == {"reasoning": {"effort": "high"}}

    record = read_log(tmp_path / "run1")
    assert record["agent"] == "coding" and record["model"] == "xiaomi/mimo-v2.6-flash"
    assert record["input_tokens"] == 1000 and record["output_tokens"] == 500
    assert record["cost_usd"] == 0.0005
    assert record["sampling_params"]["finish_reason"] == "stop"


def test_openrouter_empty_reply_and_computed_cost(tmp_path: Path, monkeypatch):
    """An empty reply comes back as "", and the cost is computed when OpenRouter does not report it."""
    monkeypatch.setattr(llm_module, "log_llm_call", None)
    llm = OpenAICompatibleLLM(None, tmp_path / "r", effort=None, client=FakeOpenRouter(content=None, cost=None))
    assert llm(agent="coding", system="s", user="u") == ""
    assert read_log(tmp_path / "r")["cost_usd"] == pytest.approx(0.00028)
    assert "extra_body" not in llm.request_args("s", "u")


def test_openrouter_needs_a_key(tmp_path: Path, monkeypatch):
    """Without OPENROUTER_API_KEY the first call fails with a clear message."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        OpenAICompatibleLLM(None, tmp_path)(agent="a", system="s", user="u")


def test_uses_role_1_logger_when_present(tmp_path: Path, monkeypatch):
    """With role 1's log_llm_call available, records go through it with run_id and runs_dir."""
    seen = []
    monkeypatch.setattr(llm_module, "log_llm_call", lambda **kw: seen.append(kw))
    OpenAICompatibleLLM(None, tmp_path / "r", client=FakeOpenRouter())(agent="a", system="s", user="u")
    assert seen[0]["run_id"] == "r" and seen[0]["runs_dir"] == tmp_path
    assert not (tmp_path / "r" / "llm_calls.jsonl").exists()


def test_gemini_sends_reasoning_effort_and_needs_its_key(tmp_path: Path, monkeypatch):
    """Gemini gets the standard reasoning_effort field and reads GEMINI_API_KEY."""
    llm = OpenAICompatibleLLM(None, tmp_path, provider="gemini", effort="low", seed=4)
    args = llm.request_args("s", "u")
    assert args["model"] == "gemini-3.5-flash-lite" and args["reasoning_effort"] == "low"
    assert "extra_body" not in args and "seed" not in args  # Gemini rejects seed with a 400
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm.client()


def test_make_llm_follows_the_config(tmp_path: Path):
    """The provider and its settings come from the llm section; OpenRouter is the default."""
    llm = make_llm({"llm": {"model": "", "temperature": 0.2, "effort": "low"}}, tmp_path, 1)
    assert isinstance(llm, OpenAICompatibleLLM) and llm.model == "xiaomi/mimo-v2.6-flash" and llm.temperature == 0.2
    assert make_llm({"llm": {"provider": "gemini"}}, tmp_path, 1).provider == "gemini"
    with pytest.raises(ValueError):
        make_llm({"llm": {"provider": "nope"}}, tmp_path, 1)


def test_cost_for_unknown_model():
    """Models without a price get no cost rather than a wrong one."""
    assert cost_usd("some-other-model", 10, 10) is None
