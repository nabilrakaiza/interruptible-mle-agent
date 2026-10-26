import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import pytest

from imle.sandbox import abandon_experiment, docker_command, run_script


def docker_running() -> bool:
    """Whether a Docker daemon answers (Colima or Docker Desktop started)."""
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True, timeout=30, check=False).returncode == 0


# The container tests use a small public image, so they run before imle-sandbox is built.
TEST_IMAGE = "python:3.13-slim"
needs_docker = pytest.mark.skipif(not docker_running(), reason="no Docker daemon running")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def docker_dir():
    """A temporary folder inside the repo: Colima's VM mounts the home folder, not pytest's /private/var temp."""
    base = ROOT / ".pytest_cache" / "docker"
    base.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(dir=base))
    yield path
    shutil.rmtree(path, ignore_errors=True)


def option(command: list[str], flag: str) -> list[str]:
    """Every value given to `flag` in a docker command."""
    return [command[i + 1] for i, part in enumerate(command) if part == flag]


def test_docker_command_sets_the_configured_limits(tmp_path: Path):
    """Memory and swap are equal, CPUs and /tmp follow the arguments, and threads are capped at the CPU count."""
    cmd = docker_command(tmp_path / "n3.py", tmp_path, "imle-x", "img", output=tmp_path / "out", cpus=2,
                         memory_gb=3.5, tmp_gb=1)
    assert option(cmd, "--memory") == option(cmd, "--memory-swap") == ["3584m"]
    assert option(cmd, "--cpus") == ["2"] and option(cmd, "--network") == ["none"]
    assert "/tmp:rw,noexec,nosuid,size=1024m" in option(cmd, "--tmpfs")
    env = option(cmd, "--env")
    assert "OMP_NUM_THREADS=2" in env and "LOKY_MAX_CPU_COUNT=2" in env and "CUDA_VISIBLE_DEVICES=" in env
    assert f"type=bind,src={tmp_path / 'out'},dst=/output" in option(cmd, "--mount") and "OUTPUT_DIR=/output" in env
    assert cmd[-3:] == ["img", "python", "n3.py"] and "--read-only" in cmd


def test_docker_command_mounts_the_harness_read_only(tmp_path: Path):
    """A harness folder is mounted read-only at /harness; without one there is no such mount."""
    cmd = docker_command(tmp_path / "s.py", tmp_path / "task", "imle-x", harness=tmp_path / "h")
    assert f"type=bind,src={tmp_path / 'h'},dst=/harness,readonly" in option(cmd, "--mount")
    assert not any("/harness" in m for m in option(docker_command(tmp_path / "s.py", tmp_path, "imle-x"), "--mount"))


def test_abandon_rejects_invalid_container():
    """Only containers this sandbox started (named imle-...) can be removed."""
    with pytest.raises(ValueError):
        abandon_experiment("unrelated-container")


def test_output_inside_task_rejected(tmp_path):
    """An output folder inside the task folder is refused, and not created."""
    task = tmp_path / "task"
    task.mkdir()

    script = task / "experiment.py"
    script.write_text(
        "print('Hello')",
        encoding="utf-8",
    )

    invalid_output = task / "output"

    with pytest.raises(ValueError):
        run_script(
            script_path=str(script),
            task_dir=str(task),
            output_dir=str(invalid_output),
            timeout_s=30,
        )

    # Invalid output directory must not be created.
    assert not invalid_output.exists()


@needs_docker
def test_docker_python_execution():
    """A locked-down container can run Python at all."""
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", "64",
            "--memory", "256m",
            "--cpus", "1",
            TEST_IMAGE,
            "python", "-c",
            "print('Sandbox test successful!')",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Sandbox test successful!" in result.stdout


@needs_docker
def test_sandbox_runs_python(docker_dir):
    """run_script runs a script and captures its output."""
    script = docker_dir / "experiment.py"
    script.write_text(
        "print('Hello from my NLP sandbox!')",
        encoding="utf-8",
    )

    result = run_script(
        script_path=str(script),
        task_dir=str(docker_dir),
        timeout_s=60,
        image=TEST_IMAGE,
        memory_gb=0.5,
    )

    assert result.exit_code == 0, result.stderr
    assert result.timed_out is False
    assert "Hello from my NLP sandbox!" in result.stdout
    assert result.wall_time_s >= 0


@needs_docker
def test_sandbox_timeout(docker_dir):
    """A script past its time limit is killed and reported as timed out."""
    script = docker_dir / "slow_experiment.py"
    script.write_text(
        "import time\ntime.sleep(60)\n",
        encoding="utf-8",
    )

    result = run_script(
        script_path=str(script),
        task_dir=str(docker_dir),
        timeout_s=5,
        image=TEST_IMAGE,
        memory_gb=0.5,
    )

    assert result.timed_out is True
    assert result.exit_code == -1


@needs_docker
def test_harness_is_read_only(docker_dir):
    """A script cannot change the harness."""
    task_dir = docker_dir / "task"
    harness_dir = docker_dir / "harness"

    task_dir.mkdir()
    harness_dir.mkdir()

    protected_file = harness_dir / "score.py"
    protected_file.write_text(
        "SCORE = 100\n",
        encoding="utf-8",
    )

    script = task_dir / "experiment.py"
    script.write_text(
        """
from pathlib import Path

protected = Path("/harness/score.py")

try:
    protected.write_text("SCORE = 0")
    print("SECURITY FAILURE")
except OSError:
    print("READ_ONLY_PROTECTION_WORKS")
""",
        encoding="utf-8",
    )

    result = run_script(
        script_path=str(script),
        task_dir=str(task_dir),
        harness_dir=str(harness_dir),
        timeout_s=60,
        image=TEST_IMAGE,
        memory_gb=0.5,
    )

    assert result.exit_code == 0, result.stderr
    assert "READ_ONLY_PROTECTION_WORKS" in result.stdout
    assert protected_file.read_text(encoding="utf-8") == "SCORE = 100\n"


@needs_docker
def test_abandon_running_container():
    """abandon_experiment removes a running sandbox container."""
    container_name = f"imle-{uuid.uuid4().hex}"

    # Start a long-running test container.
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", container_name,
            "--network", "none",
            "--read-only",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--memory", "256m",
            "--cpus", "1",
            TEST_IMAGE,
            "python", "-c",
            "import time; time.sleep(60)",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )

    try:
        time.sleep(1)

        # Ask the sandbox to abandon the experiment.
        abandoned = abandon_experiment(container_name)

        assert abandoned is True

        # Confirm that Docker removed the container.
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter",
             f"name=^{container_name}$", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )

        assert container_name not in result.stdout.splitlines()

    finally:
        # Clean up if an assertion or Docker command fails.
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )


@needs_docker
def test_sandbox_writes_output(docker_dir):
    """A script can write to /output, and the file lands in the host output folder."""
    task = docker_dir / "task"
    output = docker_dir / "output"
    task.mkdir()
    output.mkdir()
    output.chmod(0o777)  # the container runs as nobody, as DockerSandbox arranges

    script = task / "experiment.py"
    script.write_text(
        "from pathlib import Path\n"
        "Path('/output/submission.csv').write_text("
        "'prediction\\n1\\n0\\n')\n",
        encoding="utf-8",
    )

    result = run_script(
        script_path=str(script),
        task_dir=str(task),
        output_dir=str(output),
        timeout_s=60,
        image=TEST_IMAGE,
        memory_gb=0.5,
    )

    assert result.exit_code == 0, result.stderr
    assert (output / "submission.csv").exists()
    assert (
        output / "submission.csv"
    ).read_text(encoding="utf-8") == "prediction\n1\n0\n"


@needs_docker
def test_memory_limit_kills_instead_of_swapping(docker_dir):
    """A script over the memory limit is killed (exit code 137), not slowed down by swap."""
    script = docker_dir / "hog.py"
    script.write_text("x = bytearray(900 * 1024 * 1024)\nprint('survived')\n", encoding="utf-8")

    result = run_script(script_path=str(script), task_dir=str(docker_dir), timeout_s=60, image=TEST_IMAGE,
                        memory_gb=0.25)

    assert result.exit_code == 137 and "survived" not in result.stdout
