import importlib.util
import json
import sys
from pathlib import Path

from imle import checkpoint

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grade", ROOT / "scripts" / "grade.py")
grade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grade)

# Stands in for MLE-bench: scores each submission by its line count, and fails on an unknown task.
FAKE_GRADER = r"""
import json, sys
out = []
for path, comp in json.load(sys.stdin):
    if comp == "toy":
        out.append({"error": "unknown competition"})
    else:
        n = len(open(path).read().splitlines())
        out.append({"score": n, "valid_submission": True, "above_median": n > 2, "any_medal": False,
                    "gold_medal": False, "silver_medal": False, "bronze_medal": False, "ignored": 1})
print("@@GRADES@@" + json.dumps(out))
"""


def make_run(run_dir: Path, task: str, done: bool = True, top_k: bool = False) -> None:
    """A run folder with a final checkpoint and a 3-line submission (plus top-k files if asked)."""
    checkpoint.write(run_dir, 3, {"nodes": {}}, [], {"done": done, "task": task, "condition": "C1", "seed": 1,
                                                     "final_node": "n2", "final_selection": "best_val"})
    (run_dir / "submission.csv").write_text("id,y\n1,0\n2,1\n")
    if top_k:
        (run_dir / "final").mkdir()
        for rank, rows in ((1, 2), (2, 1)):
            (run_dir / "final" / f"submission_{rank}.csv").write_text("id,y\n" + "1,0\n" * rows)


def test_grades_finished_runs_and_skips_the_rest(tmp_path: Path, monkeypatch, capsys):
    """Finished runs get grade.json; unfinished, already graded and unknown-task runs are skipped."""
    monkeypatch.setattr(grade, "GRADER", FAKE_GRADER)
    make_run(tmp_path / "a", "spooky", top_k=True)
    make_run(tmp_path / "b", "spooky", done=False)
    make_run(tmp_path / "c", "toy")
    make_run(tmp_path / "d", "spooky")
    (tmp_path / "d" / "grade.json").write_text("{}")
    monkeypatch.setattr(sys, "argv", ["grade.py", str(tmp_path), "--mlebench-python", sys.executable])
    grade.main()

    result = json.loads((tmp_path / "a" / "grade.json").read_text())
    assert (result["score"], result["above_median"], result["condition"], result["seed"]) == (3, True, "C1", 1)
    assert [s["file"] for s in result["submissions"]] == ["submission.csv", "final/submission_1.csv",
                                                          "final/submission_2.csv"]
    assert "ignored" not in result
    assert not (tmp_path / "b" / "grade.json").exists() and not (tmp_path / "c" / "grade.json").exists()
    assert (tmp_path / "d" / "grade.json").read_text() == "{}"
    out = capsys.readouterr().out
    assert "not graded (unknown competition)" in out and "graded 1 run(s); 2 skipped" in out


def test_a_finished_run_without_submission_counts_as_invalid(tmp_path: Path, monkeypatch):
    """No submission.csv: graded as not submitted and not valid, without calling MLE-bench."""
    monkeypatch.setattr(grade, "GRADER", "raise SystemExit(1)")
    make_run(tmp_path / "a", "spooky")
    (tmp_path / "a" / "submission.csv").unlink()
    monkeypatch.setattr(sys, "argv", ["grade.py", str(tmp_path / "a"), "--mlebench-python", sys.executable])
    grade.main()
    result = json.loads((tmp_path / "a" / "grade.json").read_text())
    assert result["submitted"] is False and result["valid_submission"] is False
