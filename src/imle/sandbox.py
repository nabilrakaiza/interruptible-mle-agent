"""Run generated Python experiments inside isolated Docker containers.

Requirements:
    - No network or credentials
    - Restricted host filesystem access
    - Per-script timeout
    - Read-only evaluation harness
    - Capture stdout, stderr, exit code, and wall time
    - Support human-triggered experiment cancellation
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
import uuid
import contextlib


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    wall_time_s: float
    timed_out: bool


def run_script(
    script_path: str,
    task_dir: str,
    timeout_s: int = 3600,
    image: str = "python:3.11-slim",
    harness_dir: str | None = None,
    output_dir: str | None = None,
) -> SandboxResult:
    """Execute a Python script in a restricted Docker container."""

    script = Path(script_path).resolve()
    task = Path(task_dir).resolve()

    if not task.is_dir():
        raise ValueError("Task directory does not exist.")

    if not script.is_file() or not script.is_relative_to(task):
        raise ValueError("Script must exist inside the task directory.")
    container_name = f"imle-{uuid.uuid4().hex}"

    command = [
        "docker", "run",
        "--rm",
        "--name", container_name,
        "--network", "none",
        "--read-only",
        "--user", "65534:65534",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", "64",
        "--memory", "2g",
        "--cpus", "2",
        "--mount", f"type=bind,src={task},dst=/workspace,readonly",
        "--workdir", "/workspace",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=128m",
        image,
        "python", script.name,
    ]


    if harness_dir is not None:
        harness = Path(harness_dir).resolve()

        if not harness.is_dir():
            raise ValueError("Harness directory does not exist.")

        if harness == task or task in harness.parents or harness in task.parents:
            raise ValueError(
                "Harness and task directories must be separate."
            )

        command[3:3] = [
            "--mount",
            f"type=bind,src={harness},dst=/harness,readonly",
        ]


    if output_dir is not None:
        output = Path(output_dir).resolve()

        # Check that output is separate from the task directory.
        if (
            output == task
            or output in task.parents
            or task in output.parents
        ):
            raise ValueError(
                "Output and task directories must be separate."
            )

        # Check that output is separate from the harness.
        if harness_dir is not None:
            if (
                output == harness
                or output in harness.parents
                or harness in output.parents
            ):
                raise ValueError(
                    "Output and harness directories must be separate."
                )

        # Create the directory only after validation.
        output.mkdir(parents=True, exist_ok=True)

        command[3:3] = [
            "--mount",
            f"type=bind,src={output},dst=/output",
        ]



    start = time.monotonic()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )

        return SandboxResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            wall_time_s=time.monotonic() - start,
            timed_out=False,
        )

    except subprocess.TimeoutExpired as exc:
        stop_container(container_name)
        return SandboxResult(
            stdout=exc.stdout.decode(errors="replace")
            if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            stderr=exc.stderr.decode(errors="replace")
            if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
            exit_code=-1,
            wall_time_s=time.monotonic() - start,
            timed_out=True,
        )
def stop_container(container_name: str) -> None:
    """Force-remove a sandbox container if it still exists."""
    if not container_name.startswith("imle-"):
        raise ValueError("Invalid sandbox container name.")

    with contextlib.suppress(subprocess.TimeoutExpired):
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

def abandon_experiment(container_name: str) -> bool:
    """Stop a running experiment container.

    Returns True if Docker removed the container.
    Returns False if Docker could not remove it.
    """
    if not container_name.startswith("imle-"):
        raise ValueError("Invalid sandbox container name.")

    result = subprocess.run(
        ["docker", "rm", "-f", container_name],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    return result.returncode == 0
