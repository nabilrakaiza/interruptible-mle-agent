"""Leakage stress test: A1's screen on planted leaks and clean controls.

Role 3's reliability check (docs/experiments.md). scripts/leakage/ holds one planted
script per leakage type and a clean control that does the same job correctly:

    planted_target_feature / clean_target_feature   R1, the target among the features
    planted_test_stats     / clean_test_stats       R2, statistics computed on predict.csv rows
    planted_val_in_train   / clean_val_in_train     R3, validation rows used to fit the scored model
    planted_harness_access / clean_harness_access   R0, reading the harness outside ./input

A planted script counts as detected when the screen flags it at all (any rule, warn or
leak), and as detected by the expected rule when that rule fires. A clean control
counts as a false positive when anything is flagged. `--scripts` adds real node
scripts (no ground truth): their flag rates are an upper bound on false positives
that needs a manual look.

    python scripts/leakage_stress_test.py
    python scripts/leakage_stress_test.py --execute            # also run every script on synthetic data
    python scripts/leakage_stress_test.py --scripts 'runs/*/nodes/*/solution.py'
    python scripts/leakage_stress_test.py --llm-review         # adds A1's LLM review: real API calls

Writes one row per script to --out (default results/leakage_stress.csv) and the
rates to the same name with _summary.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from imle.agents import evaluation as a1
from imle.agents.coding import with_output_dir

LEAKAGE_DIR = Path(__file__).resolve().parent / "leakage"
EXPECTED_RULE = {
    "target_feature": "R1_target_as_feature",
    "test_stats": "R2_test_statistics",
    "val_in_train": "R3_val_in_training",
    "harness_access": "R0_harness_access",
}


def fixtures(leakage_dir: Path = LEAKAGE_DIR) -> list[tuple[Path, str, str]]:
    """(path, kind, leak type) for every planted script and clean control, in a fixed order."""
    out = []
    for kind in ("planted", "clean"):
        for path in sorted(leakage_dir.glob(f"{kind}_*.py")):
            leak_type = path.stem[len(kind) + 1:]
            if leak_type not in EXPECTED_RULE:
                raise ValueError(f"{path.name}: unknown leakage type {leak_type!r}")
            out.append((path, kind, leak_type))
    return out


def execute(script: Path, work_dir: Path, seed: int = 0) -> bool:
    """Run a script on the synthetic dataset in its own workspace; True if it wrote predictions."""
    spec = importlib.util.spec_from_file_location("make_data", LEAKAGE_DIR / "make_data.py")
    make_data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(make_data)

    workspace = work_dir / script.stem
    if workspace.exists():
        shutil.rmtree(workspace)
    make_data.make(workspace, seed)
    output = workspace / "output"
    output.mkdir()
    runnable = workspace / script.name
    runnable.write_text(with_output_dir(script.read_text(encoding="utf-8"), str(output)), encoding="utf-8")
    done = subprocess.run([sys.executable, "-I", runnable.name], cwd=workspace, capture_output=True, text=True,
                          timeout=120, check=False)
    return done.returncode == 0 and (output / "predictions.csv").exists()


def screen_rows(items: list[tuple[Path, str, str]], llm=None, work_dir: Path | None = None) -> pd.DataFrame:
    """One row per script: what the screen flagged, and whether that was the right call."""
    rows = []
    for path, kind, leak_type in items:
        report = a1.screen_script(path.read_text(encoding="utf-8"), llm=llm)
        rules = sorted({f.rule for f in report.flags})
        row = {"script": path.name, "kind": kind, "leak_type": leak_type, "verdict": report.verdict,
               "rules": ";".join(rules), "flagged": bool(report.flags),
               "expected_rule_hit": EXPECTED_RULE.get(leak_type, "") in rules,
               "rules_flagged": any(f.source == "rules" for f in report.flags),
               "llm_flagged": any(f.source == "llm" for f in report.flags)}
        if work_dir is not None and kind in ("planted", "clean"):
            row["ran"] = execute(path, work_dir)
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(rows: pd.DataFrame) -> pd.DataFrame:
    """Detection rate per leakage type, false-positive rate on the clean controls, flag rate on real scripts."""
    out = []
    planted = rows[rows.kind == "planted"]
    for leak_type, group in planted.groupby("leak_type", sort=True):
        out.append({"measure": "detection_rate", "leak_type": leak_type, "n": len(group),
                    "rate": group["flagged"].mean(), "expected_rule_rate": group["expected_rule_hit"].mean()})
    if len(planted):
        out.append({"measure": "detection_rate", "leak_type": "all", "n": len(planted),
                    "rate": planted["flagged"].mean(), "expected_rule_rate": planted["expected_rule_hit"].mean()})
    clean = rows[rows.kind == "clean"]
    if len(clean):
        out.append({"measure": "false_positive_rate", "leak_type": "all", "n": len(clean),
                    "rate": clean["flagged"].mean(), "expected_rule_rate": None})
    real = rows[rows.kind == "real"]
    if len(real):
        out.append({"measure": "real_script_flag_rate", "leak_type": "all", "n": len(real),
                    "rate": real["flagged"].mean(), "expected_rule_rate": None})
        out.append({"measure": "real_script_leak_rate", "leak_type": "all", "n": len(real),
                    "rate": (real["verdict"] == "leak").mean(), "expected_rule_rate": None})
    return pd.DataFrame(out)


def main(argv: list[str] | None = None) -> pd.DataFrame:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("results/leakage_stress.csv"))
    parser.add_argument("--execute", action="store_true", help="also run each fixture on synthetic data")
    parser.add_argument("--work-dir", type=Path, help="where --execute builds workspaces (default: next to --out)")
    parser.add_argument("--scripts", action="append", default=[], help="glob of real node scripts to screen too")
    parser.add_argument("--llm-review", action="store_true", help="add A1's LLM review (real API calls)")
    parser.add_argument("--config", type=Path, default=Path("configs/conditions/c1_autonomous.yaml"),
                        help="condition file whose llm settings --llm-review uses")
    args = parser.parse_args(argv)

    llm = None
    if args.llm_review:
        from dotenv import load_dotenv

        from imle.controller import load_config
        from imle.llm import make_llm

        load_dotenv()
        llm = make_llm(load_config(args.config), args.out.parent / "leakage_llm", seed=0)

    items = fixtures()
    for pattern in args.scripts:
        items += [(Path(p), "real", "") for p in sorted(glob.glob(pattern, recursive=True))]
    work_dir = (args.work_dir or args.out.parent / "leakage_work") if args.execute else None
    rows = screen_rows(items, llm=llm, work_dir=work_dir)
    summary = summarise(rows)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.out, index=False)
    summary.to_csv(args.out.with_name(args.out.stem + "_summary.csv"), index=False)
    print(summary.to_string(index=False))
    if "ran" in rows:
        print(f"ran on synthetic data: {int(rows['ran'].sum())} of {len(rows[rows.kind != 'real'])} fixtures")
    print(f"wrote {args.out}")
    return rows


if __name__ == "__main__":
    main()
