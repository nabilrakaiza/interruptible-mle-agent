from pathlib import Path

import pytest

import imle.sandbox
from imle.execution import DockerSandbox, SubprocessSandbox, make_sandbox


def test_docker_sandbox_calls_role_1_run_script(tmp_path: Path, monkeypatch):
    """The Docker backend hands role 1's run_script the workspace, output folder, image and a whole-second timeout."""
    calls = []
    monkeypatch.setattr(imle.sandbox, "run_script", lambda **kw: calls.append(kw) or "result", raising=False)
    output = tmp_path / "nodes" / "n0" / "output"
    output.mkdir(parents=True)
    sandbox = DockerSandbox("my-image")
    assert sandbox.run(tmp_path / "workspace" / "n0.py", tmp_path / "workspace", output, 12.2) == "result"
    assert calls == [{
        "script_path": str(tmp_path / "workspace" / "n0.py"),
        "task_dir": str(tmp_path / "workspace"),
        "timeout_s": 13,
        "image": "my-image",
        "output_dir": str(output),
        "cpus": 2,
        "memory_gb": 4,
    }]
    assert output.stat().st_mode & 0o777 == 0o777
    assert sandbox.output_path(output) == "/output"


def test_subprocess_sandbox_runs_and_times_out(tmp_path: Path):
    """The local backend captures output and exit code, and reports a timeout instead of raising."""
    (tmp_path / "ok.py").write_text("import sys\nprint('hi')\nsys.exit(3)\n")
    (tmp_path / "slow.py").write_text("import time\nprint('start', flush=True)\ntime.sleep(10)\n")
    sandbox = SubprocessSandbox()
    ok = sandbox.run(tmp_path / "ok.py", tmp_path, tmp_path, 10)
    assert (ok.stdout, ok.exit_code, ok.timed_out) == ("hi\n", 3, False)
    slow = sandbox.run(tmp_path / "slow.py", tmp_path, tmp_path, 1)
    assert slow.timed_out and slow.exit_code == -1


def test_subprocess_sandbox_caps_threads_at_the_configured_cpus(tmp_path: Path):
    """With cpus set, numpy, joblib and torch see that many threads, as in the Docker sandbox; a GPU is never visible."""
    (tmp_path / "env.py").write_text("import os\nprint(os.environ.get('OMP_NUM_THREADS'), os.environ.get('LOKY_MAX_CPU_COUNT'), "
                                     "repr(os.environ.get('CUDA_VISIBLE_DEVICES')))\n")
    assert SubprocessSandbox(2).run(tmp_path / "env.py", tmp_path, tmp_path, 10).stdout == "2 2 ''\n"
    assert SubprocessSandbox().run(tmp_path / "env.py", tmp_path, tmp_path, 10).stdout.endswith("''\n")
    assert make_sandbox({"sandbox": {"backend": "subprocess", "cpus": 3}}).cpus == 3


def test_make_sandbox():
    """The backend comes from the argument, then the config, then defaults to Docker."""
    assert isinstance(make_sandbox({}), DockerSandbox)
    assert isinstance(make_sandbox({"sandbox": {"backend": "subprocess"}}), SubprocessSandbox)
    docker = make_sandbox({"sandbox": {"image": "x", "cpus": 3, "memory_gb": 5}})
    assert (docker.image, docker.cpus, docker.memory_gb) == ("x", 3, 5)
    assert isinstance(make_sandbox({"sandbox": {"backend": "docker"}}, "subprocess"), SubprocessSandbox)
    with pytest.raises(ValueError):
        make_sandbox({}, "vm")
