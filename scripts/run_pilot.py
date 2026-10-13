
"""Run a small local experiment using the Docker sandbox."""

import argparse
import json
import tempfile
from pathlib import Path

from load_config import load_config
from imle.sandbox import run_script


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "configs" / "pilot.yaml"),
    )
    args = parser.parse_args()

    config = load_config(
        ROOT / "configs" / "base.yaml",
        args.config,
    )

    timeout = config["budget"]["script_timeout_s"]

    print("Starting pilot experiment...")
    print(f"Condition: {config['condition']}")
    print(f"Script timeout: {timeout} seconds")

    with tempfile.TemporaryDirectory() as task_dir:
        script = Path(task_dir) / "experiment.py"

        script.write_text(
            "print('Hello from the NLP pilot experiment!')\n"
            "print('Experiment completed successfully.')\n",
            encoding="utf-8",
        )

        result = run_script(
            script_path=str(script),
            task_dir=task_dir,
            timeout_s=timeout,
        )

    print("\nExperiment results:")
    print(json.dumps({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "wall_time_s": result.wall_time_s,
        "timed_out": result.timed_out,
    }, indent=2))

    if result.exit_code != 0 or result.timed_out:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
