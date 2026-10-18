import json
from pathlib import Path
from types import SimpleNamespace

from imle import llm as llm_module
from imle.llm import AnthropicLLM, cost_usd


class FakeStream:
    """Context manager standing in for the SDK's message stream."""

    def __init__(self, message):
        """`message` is what get_final_message returns."""
        self.message = message

    def __enter__(self):
        """Enter the stream."""
        return self

    def __exit__(self, *exc):
        """Leave the stream without suppressing errors."""
        return False

    def get_final_message(self):
        """The finished message."""
        return self.message


class FakeClient:
    """Records the arguments of each beta.messages.stream call and returns a fixed message."""

    def __init__(self, text: str = "PLAN: x\n```python\npass\n```", model: str = "claude-opus-5-5"):
        """Every call returns `text`, as if served by `model`."""
        self.calls = []
        message = SimpleNamespace(
            content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
            stop_reason="end_turn",
            model=model,
            usage=SimpleNamespace(input_tokens=1000, output_tokens=500),
        )

        def stream(**kwargs):
            """Record the request and return the fake stream."""
            self.calls.append(kwargs)
            return FakeStream(message)

        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=stream))


def test_request_and_log(tmp_path: Path, monkeypatch):
    """One call sends effort and fallbacks, returns only the text, and logs tokens and cost."""
    monkeypatch.setattr(llm_module, "log_llm_call", None)
    client = FakeClient()
    llm = AnthropicLLM("${LLM_MODEL}", tmp_path / "run1", effort="high", seed=3, client=client)
    assert llm(agent="coding", system="sys", user="hello") == "PLAN: x\n```python\npass\n```"

    sent = client.calls[0]
    assert sent["model"] == "claude-opus-5-5"
    assert sent["output_config"] == {"effort": "high"}
    assert sent["fallbacks"] == "default" and sent["betas"] == ["server-side-fallback-2026-07-01"]
    assert sent["messages"] == [{"role": "user", "content": "hello"}] and sent["system"] == "sys"
    assert "temperature" not in sent

    record = json.loads((tmp_path / "run1" / "llm_calls.jsonl").read_text())
    assert record["agent"] == "coding" and record["seed"] == 3 and record["run_id"] == "run1"
    assert record["input_tokens"] == 1000 and record["cost_usd"] == 0.014
    assert record["sampling_params"]["stop_reason"] == "end_turn"


def test_no_fallbacks_for_models_without_them(tmp_path: Path):
    """Haiku has no server-side fallback, so the request leaves it out."""
    args = AnthropicLLM("claude-haiku-5-5", tmp_path, client=FakeClient()).request_args("s", "u")
    assert "fallbacks" not in args and "betas" not in args


def test_uses_role_1_logger_when_present(tmp_path: Path, monkeypatch):
    """With role 1's log_llm_call available, records go through it with run_id and runs_dir."""
    seen = []
    monkeypatch.setattr(llm_module, "log_llm_call", lambda **kw: seen.append(kw))
    AnthropicLLM("claude-opus-5-5", tmp_path / "r", client=FakeClient())(agent="a", system="s", user="u")
    assert seen[0]["run_id"] == "r" and seen[0]["runs_dir"] == tmp_path
    assert not (tmp_path / "r" / "llm_calls.jsonl").exists()


def test_cost_for_unknown_model():
    """Models without a price get no cost rather than a wrong one."""
    assert cost_usd("some-other-model", 10, 10) is None
