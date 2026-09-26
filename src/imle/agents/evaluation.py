"""A1: evaluation agent.

Runs once per run:
    - inspect data files and task description
    - build disjoint train / validation / probe splits
    - write the scoring harness, then freeze it (read-only to A3)

Runs per candidate script:
    - screen for target leakage and unused data sources before execution
"""
