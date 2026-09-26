"""Structured logging for every LLM call and every execution.

Each LLM call records: agent, prompt, completion, model version string,
sampling parameters, input/output tokens, latency, timestamp, seed.
Written to runs/<run_id>/llm_calls.jsonl.
"""
