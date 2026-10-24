"""Run generated Python experiments inside isolated Docker containers.

Requirements:
    - No network or credentials
    - Restricted host filesystem access
    - Per-script timeout
    - Read-only evaluation harness
    - Capture stdout, stderr, exit code, and wall time
    - Support human-triggered experiment cancellation

Limits match what A3's prompt states (`sandbox.cpus`, `sandbox.memory_gb` in
configs/base.yaml). Swap is set equal to memory, so a script over the limit is
killed at once (exit code 137) instead of swapping. The thread variables cap
numpy, scikit-learn and torch at the CPU limit, since a container still sees
every core of the host.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
import uuid
import contextlib

DEFAULT_IMAGE = "imle-sandbox:latest"

# Variables that cap the threads numpy, scikit-learn (joblib) and torch use.
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
               "NUMEXPR_NUM_THREADS", "LOKY_MAX_CPU_COUNT")


@dataclass
class SandboxResult:
    """What one script execution produced."""

    stdout: str
    stderr: str
    exit_code: int
    wall_time_s: float
    timed_out: bool


def _separate(a: Path, b: Path) -> bool:
    """Whether neither folder is the other or inside the other."""
    return a != b and a not in b.parents and b not in a.parents


def docker_command(
    script: Path,
    task: Path,
    container_name: str,
    image: str = DEFAULT_IMAGE,
    harness: Path | None = None,
    output: Path | None = None,
    cpus: float = 2,
    memory_gb: float = 4,
    tmp_gb: float = 1,
) -> list[str]:
    """The `docker run` command for one script: no network, read-only root and task folder, fixed limits."""
    memory = f"{int(memory_gb * 1024)}m"
    env = {v: str(max(1, int(cpus))) for v in THREAD_VARS}
    env.update({
        "CUDA_VISIBLE_DEVICES": "",   # no GPU, as on every machine the experiments run on
        "HOME": "/tmp",               # libraries that cache under ~ (matplotlib, torch) need a writable home
        "MPLCONFIGDIR": "/tmp",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    })
    command = [
        "docker", "run",
        "--rm",
        "--name", container_name,
        "--network", "none",
        "--read-only",
        "--user", "65534:65534",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", "256",        # threads count too: torch and joblib start several per core
        "--memory", memory,
        "--memory-swap", memory,
        "--cpus", str(cpus),
        "--mount", f"type=bind,src={task},dst=/workspace,readonly",
        "--workdir", "/workspace",
        "--tmpfs", f"/tmp:rw,noexec,nosuid,size={int(tmp_gb * 1024)}m",
    ]
    if harness is not None:
        command += ["--mount", f"type=bind,src={harness},dst=/harness,readonly"]
    if output is not None:
        command += ["--mount", f"type=bind,src={output},dst=/output"]
    for key, value in env.items():
        command += ["--env", f"{key}={value}"]
    return command + [image, "python", script.name]


def run_script(
    script_path: str,
    task_dir: str,
    timeout_s: int = 3600,
    image: str = DEFAULT_IMAGE,
    harness_dir: str | None = None,
    output_dir: str | None = None,
    cpus: float = 2,
    memory_gb: float = 4,
    tmp_gb: float = 1,
) -> SandboxResult:
    """Execute a Python script in a restricted Docker container."""

    script = Path(script_path).resolve()
    task = Path(task_dir).resolve()

    if not task.is_dir():
        raise ValueError("Task directory does not exist.")

    if not script.is_file() or not script.is_relative_to(task):
        raise ValueError("Script must exist inside the task directory.")

    harness = None
    if harness_dir is not None:
        harness = Path(harness_dir).resolve()
        if not harness.is_dir():
            raise ValueError("Harness directory does not exist.")
        if not _separate(harness, task):
            raise ValueError("Harness and task directories must be separate.")

    output = None
    if output_dir is not None:
        output = Path(output_dir).resolve()
        if not _separate(output, task):
            raise ValueError("Output and task directories must be separate.")
        if harness is not None and not _separate(output, harness):
            raise ValueError("Output and harness directories must be separate.")
        # Create the directory only after validation.
        output.mkdir(parents=True, exist_ok=True)

    container_name = f"imle-{uuid.uuid4().hex}"
    command = docker_command(script, task, container_name, image, harness, output, cpus, memory_gb, tmp_gb)

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
    with contextlib.suppress(subprocess.TimeoutExpired):
        abandon_experiment(container_name)


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
