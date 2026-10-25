"""Sandbox backends the controller runs generated scripts with.

Both use the same layout. The run's workspace folder (scripts plus ./input) is
the working directory and is read-only to the script. Each node gets its own
output folder, which the script reaches through the OUTPUT_DIR variable the
controller writes at the top of the script.

DockerSandbox wraps role 1's `imle.sandbox.run_script`. SubprocessSandbox runs
the script as a plain local process; it has no isolation and is meant for
machines without Docker and for tests.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from imle.sandbox import DEFAULT_IMAGE, THREAD_VARS


@dataclass
class ExecOutcome:
    """What one script execution produced. Same fields as role 1's SandboxResult."""

    stdout: str
    stderr: str
    exit_code: int
    wall_time_s: float
    timed_out: bool


class DockerSandbox:
    """Role 1's Docker sandbox: workspace mounted read-only at /workspace, output folder at /output."""

    def __init__(self, image: str = DEFAULT_IMAGE, cpus: float = 2, memory_gb: float = 4) -> None:
        """`image` must contain Python and the packages listed in agents/coding.py; the limits are A3's prompt's."""
        self.image = image
        self.cpus = cpus
        self.memory_gb = memory_gb

    def output_path(self, output_dir: Path) -> str:
        """Where the script sees `output_dir`: always /output inside the container."""
        return "/output"

    def run(self, script_path: Path, workspace: Path, output_dir: Path, timeout_s: float):
        """Run the script in a fresh container with no network, and kill it after `timeout_s`."""
        from imle.sandbox import run_script

        # The container runs as nobody (uid 65534), which cannot write to a 755 folder on Linux.
        output_dir.chmod(0o777)
        return run_script(
            script_path=str(script_path),
            task_dir=str(workspace),
            timeout_s=max(1, math.ceil(timeout_s)),
            image=self.image,
            output_dir=str(output_dir),
            cpus=self.cpus,
            memory_gb=self.memory_gb,
        )


class SubprocessSandbox:
    """A local process with this Python interpreter. No isolation; for local testing only."""

    def __init__(self, cpus: int | None = None) -> None:
        """`cpus` caps the threads the script's libraries use, like Docker's CPU limit; None leaves them uncapped.

        Without a cap, a script on an 8-core laptop uses all 8 cores while A3's prompt says
        `sandbox.cpus`, so local runs would be faster than Docker runs of the same condition.
        """
        self.cpus = cpus

    def output_path(self, output_dir: Path) -> str:
        """Where the script sees `output_dir`: its absolute path on this machine."""
        return str(output_dir.resolve())

    def run(self, script_path: Path, workspace: Path, output_dir: Path, timeout_s: float) -> ExecOutcome:
        """Run the script with `workspace` as working directory, and kill it after `timeout_s`."""
        start = time.monotonic()
        try:
            # No GPU, as in the Docker sandbox: Colab and Kaggle machines may have one, and torch would use it.
            env = {**os.environ, "CUDA_VISIBLE_DEVICES": ""}
            if self.cpus is not None:
                env.update({v: str(self.cpus) for v in THREAD_VARS})
            p = subprocess.run(
                [sys.executable, script_path.name],
                cwd=workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            return ExecOutcome(_text(e.stdout), _text(e.stderr), -1, time.monotonic() - start, True)
        return ExecOutcome(p.stdout, p.stderr, p.returncode, time.monotonic() - start, False)


def _text(value: str | bytes | None) -> str:
    """Captured output as text, whether the timeout handed back bytes, text or nothing."""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def make_sandbox(cfg: dict, backend: str | None = None) -> DockerSandbox | SubprocessSandbox:
    """The sandbox named by `backend`, or by `sandbox.backend` in the config (default docker)."""
    settings = cfg.get("sandbox") or {}
    backend = backend or settings.get("backend", "docker")
    if backend == "docker":
        return DockerSandbox(settings.get("image", DEFAULT_IMAGE), settings.get("cpus", 2),
                             settings.get("memory_gb", 4))
    if backend == "subprocess":
        return SubprocessSandbox(settings.get("cpus"))
    raise ValueError(f"unknown sandbox backend {backend!r}")
