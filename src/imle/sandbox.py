"""Isolated execution of generated scripts.

Requirements:
    - no network, no credentials, no host filesystem access beyond the task dir
    - per-script timeout
    - harness mounted read-only
    - capture stdout, stderr, exit code, wall time
    - support termination for the `abandon` intervention
"""
