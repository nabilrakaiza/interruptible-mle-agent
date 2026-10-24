
import subprocess


def test_docker_python_execution():
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
            "python:3.11-slim",
            "python", "-c",
            "print('Sandbox test successful!')",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Sandbox test successful!" in result.stdout


from imle.sandbox import run_script


def test_sandbox_runs_python(tmp_path):
    script = tmp_path / "experiment.py"
    script.write_text(
        "print('Hello from my NLP sandbox!')",
        encoding="utf-8",
    )

    result = run_script(
        script_path=str(script),
        task_dir=str(tmp_path),
        timeout_s=30,
    )

    assert result.exit_code == 0
    assert result.timed_out is False
    assert "Hello from my NLP sandbox!" in result.stdout
    assert result.wall_time_s >= 0

def test_sandbox_timeout(tmp_path):
    script = tmp_path / "slow_experiment.py"
    script.write_text(
        "import time\ntime.sleep(60)\n",
        encoding="utf-8",
    )

    result = run_script(
        script_path=str(script),
        task_dir=str(tmp_path),
        timeout_s=5,
    )

    assert result.timed_out is True
    assert result.exit_code == -1
from imle.sandbox import abandon_experiment


def test_abandon_rejects_invalid_container():
    import pytest

    with pytest.raises(ValueError):
        abandon_experiment("unrelated-container")


def test_harness_is_read_only(tmp_path):
    task_dir = tmp_path / "task"
    harness_dir = tmp_path / "harness"

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
        timeout_s=30,
    )

    assert result.exit_code == 0, result.stderr
    assert "READ_ONLY_PROTECTION_WORKS" in result.stdout
    assert protected_file.read_text(encoding="utf-8") == "SCORE = 100\n"


import subprocess
import time
import uuid

from imle.sandbox import abandon_experiment


def test_abandon_running_container():
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
            "python:3.11-slim",
            "python", "-c",
            "import time; time.sleep(60)",
        ],
        capture_output=True,
        text=True,
        timeout=30,
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

def test_sandbox_writes_output(tmp_path):
    task = tmp_path / "task"
    output = tmp_path / "output"
    task.mkdir()

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
        timeout_s=30,
    )

    assert result.exit_code == 0, result.stderr
    assert (output / "submission.csv").exists()
    assert (
        output / "submission.csv"
    ).read_text(encoding="utf-8") == "prediction\n1\n0\n"


import pytest


def test_output_inside_task_rejected(tmp_path):
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
