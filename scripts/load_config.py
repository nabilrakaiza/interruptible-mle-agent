
"""Load and merge experiment configurations."""

import argparse
import json
from copy import deepcopy
from pathlib import Path

import yaml


def deep_merge(base, overrides):
    """Merge nested dictionaries without removing unspecified settings."""
    result = deepcopy(base)

    for key, value in overrides.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_config(base_path, override_path):
    """Load base configuration and apply experiment overrides."""
    with Path(base_path).open(encoding="utf-8") as file:
        base = yaml.safe_load(file) or {}

    with Path(override_path).open(encoding="utf-8") as file:
        overrides = yaml.safe_load(file) or {}

    if not isinstance(base, dict) or not isinstance(overrides, dict):
        raise ValueError("Configuration files must contain YAML mappings.")

    return deep_merge(base, overrides)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="configs/base.yaml")
    parser.add_argument("--override", required=True)
    args = parser.parse_args()

    config = load_config(args.base, args.override)
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
