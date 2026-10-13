
import json

from imle.llm_log import log_llm_call


def test_llm_logging(tmp_path):
    log_llm_call(
        run_id="test_run",
        agent="A3",
        model="example-model",
        prompt="Write a Python script",
        completion="print('Hello')",
        input_tokens=100,
        output_tokens=50,
        latency_s=1.5,
        seed=42,
        sampling_params={"temperature": 0.7},
        cost_usd=0.001,
        runs_dir=tmp_path,
    )

    log_file = tmp_path / "test_run" / "llm_calls.jsonl"

    assert log_file.exists()

    with log_file.open(encoding="utf-8") as file:
        record = json.loads(file.readline())

    assert record["agent"] == "A3"
    assert record["model"] == "example-model"
    assert record["input_tokens"] == 100
    assert record["output_tokens"] == 50
    assert record["cost_usd"] == 0.001
    assert record["seed"] == 42
