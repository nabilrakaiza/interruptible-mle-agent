
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "scripts" / "load_config.py"

spec = importlib.util.spec_from_file_location("load_config", LOADER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_pilot_configuration():
    config = module.load_config(
        ROOT / "configs" / "base.yaml",
        ROOT / "configs" / "pilot.yaml",
    )

    assert config["budget"]["wall_clock_s"] == 300
    assert config["budget"]["script_timeout_s"] == 60
    assert config["budget"]["max_nodes"] == 3
    assert config["search"]["num_drafts"] == 1

    # Check that unchanged settings are preserved.
    assert config["search"]["debug_prob"] == 0.5
    assert config["splits"]["probe_fraction"] == 0.1
    assert config["condition"] == "C1"
    assert config["monitors"] == []

import subprocess
import sys


def test_pilot_runner():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_pilot.py"),
            "--config",
            str(ROOT / "configs" / "pilot.yaml"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Experiment completed successfully." in result.stdout
    assert '"timed_out": false' in result.stdout
