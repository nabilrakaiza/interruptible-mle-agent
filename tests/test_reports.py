import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

from imle import checkpoint, monitor
from imle.apply import apply_pending
from imle.intervention import Action
from imle.state import SearchState
from imle.tree import Node, NodeStatus, Operator, Tree

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    """A script from scripts/ as a module."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cost_report, outcomes, interaction_cost = load("cost_report"), load("outcomes"), load("interaction_cost")

GRADE = {"task": "toy", "condition": "C1", "seed": 0, "score": 0.30, "valid_submission": True, "above_median": True,
         "any_medal": False, "median_threshold": 0.40, "bronze_threshold": 0.25, "silver_threshold": 0.20,
         "gold_threshold": 0.10, "is_lower_better": True}


def make_run(run_dir: Path, condition: str = "C1", elapsed_s: float = 3600) -> Tree:
    """A finished run, lower is better: n0 (test 0.30), n1 (best val, test 0.31), n2 (worse val, test 0.24)."""
    tree = Tree(higher_is_better=False)
    for nid, val, test, done_at in (("n0", 0.30, 0.30, "00:10"), ("n1", 0.20, 0.31, "00:20"),
                                    ("n2", 0.35, 0.24, "00:30")):
        tree.add(Node(id=nid, operator=Operator.DRAFT, status=NodeStatus.WORKING, val_score=val, probe_score=val,
                      test_score=test, finished_at=f"2026-10-24T00:{done_at}+00:00"))
    status = {"done": True, "task": "toy", "condition": condition, "seed": 0, "elapsed_s": elapsed_s}
    checkpoint.write(run_dir, 4, tree.model_dump(mode="json"), [], status)
    calls = [{"agent": "coding", "model": "m", "prompt": "p" * 100, "completion": "c", "input_tokens": 1_000_000,
              "output_tokens": 500_000, "cost_usd": 0.0, "sampling_params": {"served_by": "Baidu"}}] * 2
    (run_dir / "llm_calls.jsonl").write_text("".join(json.dumps(c) + "\n" for c in calls))
    return tree


def test_cost_report_reference_cost_and_projection(tmp_path: Path):
    """Reference cost is tokens times the price; the projection scales cost per hour by budget and runs."""
    make_run(tmp_path / "r1")
    row = cost_report.run_row(tmp_path / "r1", price_in=0.1, price_out=0.2)
    assert (row["calls"], row["input_tokens"], row["output_tokens"], row["nodes"]) == (2, 2_000_000, 1_000_000, 3)
    assert row["reference_cost_usd"] == 0.4 and row["reference_cost_per_hour"] == 0.4 and row["cost_usd"] == 0.0
    assert row["tokens_per_node"] == 1_000_000 and row["served_by"] == "Baidu 2"
    schedule = tmp_path / "schedule.yaml"
    schedule.write_text("defaults: {budget_hours: 2}\ntasks: [toy, other]\nblocks: [{config: x, seeds: [0, 1]}]\n")
    import pandas as pd
    proj = cost_report.project(pd.DataFrame([row]), schedule)
    assert proj["projected_usd"].tolist() == [1.6, 1.6] and proj["from"].tolist() == ["this task's pilots",
                                                                                       "all pilots"]


def test_outcomes_medals_follow_mle_bench_rules():
    """Lower is better: at the threshold counts as reaching it; the median must be beaten strictly."""
    assert outcomes.medal_flags(0.25, GRADE)["any_medal"] and not outcomes.medal_flags(0.2501, GRADE)["any_medal"]
    assert not outcomes.medal_flags(0.40, GRADE)["above_median"]
    assert outcomes.medal_flags(None, GRADE)["valid_submission"] is False


def test_outcomes_post_hoc_rows(tmp_path: Path):
    """C2 takes the best test score of any node; C3 the best among the top k by validation."""
    make_run(tmp_path / "r1")
    (tmp_path / "r1" / "grade.json").write_text(json.dumps(GRADE))
    rows = outcomes.collect([tmp_path / "r1"], k=2).set_index("condition")
    assert rows.loc["C1", "score"] == 0.30 and not rows.loc["C1", "any_medal"]
    assert rows.loc["C2 (post hoc)", "score"] == 0.24 and rows.loc["C2 (post hoc)", "any_medal"]
    assert rows.loc["C3 (post hoc, k=2)", "score"] == 0.30  # top 2 by val: n1 (0.31) and n0 (0.30)
    table = outcomes.rates(rows.reset_index(), ["condition"])
    assert table.set_index("condition").loc["C2 (post hoc)", "any_medal"] == "100% [100, 100]"


def test_bootstrap_ci_brackets_the_mean():
    """The interval contains the sample mean and stays within [0, 1] for rates."""
    lo, hi = outcomes.bootstrap_ci(np.array([0, 1, 1, 0, 1, 1, 1, 0], dtype=float))
    assert 0 <= lo < 0.625 < hi <= 1


def test_interaction_cost_counts_timing_and_human_time(tmp_path: Path):
    """Applied and dropped interventions are counted, placed on the node axis, and timed from the dashboard log."""
    run = tmp_path / "r1"
    tree = make_run(run, condition="C6")
    (run / monitor.LOG_NAME).write_text(
        json.dumps({"ts": "2026-10-24T00:00:00+00:00", "session": "s", "event": "session_start"}) + "\n")
    monitor.queue_intervention(run, Action.PRUNE, "n2", session="s")
    monitor.queue_intervention(run, Action.OVERRIDE, "n9", session="s")
    monitor.queue_intervention(run, Action.REBUDGET, None, {"seconds": 60}, source="divergence_prune")
    apply_pending(run, tree, [], SearchState())
    items = interaction_cost.run_interventions(run).set_index("action")
    assert items.loc["prune", "outcome"] == "applied" and items.loc["override", "outcome"] == "dropped"
    assert items.loc["prune", "timing"] == 1.0 and items.loc["rebudget", "source_kind"] == "policy"
    assert items.loc["prune", "human_s"] > 0 and np.isnan(items.loc["rebudget", "human_s"])
    row = interaction_cost.per_run(run, items.reset_index())
    assert (row["queued"], row["applied"], row["dropped"], row["prune"], row["rebudget"]) == (3, 2, 1, 1, 1)
    assert row["lost_wall_clock_s"] == 0.0


def test_reports_run_end_to_end(tmp_path: Path, monkeypatch, capsys):
    """Each script's command line writes its summary.md."""
    make_run(tmp_path / "runs" / "r1")
    (tmp_path / "runs" / "r1" / "grade.json").write_text(json.dumps(GRADE))
    for module, name in ((cost_report, "cost"), (outcomes, "outcomes"), (interaction_cost, "interaction")):
        monkeypatch.setattr(sys, "argv", [name, str(tmp_path / "runs"), "--out", str(tmp_path / name)])
        module.main()
        assert (tmp_path / name / "summary.md").exists()
    assert "# Interaction cost" in capsys.readouterr().out
