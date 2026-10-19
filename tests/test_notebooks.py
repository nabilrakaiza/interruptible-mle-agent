import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("*.ipynb"))
SECRET = re.compile(r"ghp_|github_pat_|AIza[0-9A-Za-z_-]{10}|sk-or-|sk-ant-")


def cells(path: Path, kind: str = "code") -> list[str]:
    """The source of every cell of one kind in a notebook."""
    nb = json.loads(path.read_text())
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == kind]


def cell_containing(path: Path, text: str) -> str:
    """The first code cell that contains `text`."""
    return next(src for src in cells(path) if text in src)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebooks_are_clean(path: Path):
    """Valid nbformat 4, no saved outputs, no keys or tokens, and every code cell compiles."""
    assert len(NOTEBOOKS) == 2
    nb = json.loads(path.read_text())
    assert nb["nbformat"] == 4
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == [] and cell["execution_count"] is None
    assert not SECRET.search(path.read_text())
    for src in cells(path):
        compile(src, path.name, "exec")


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_git_errors_never_show_the_token(path: Path):
    """The clone helper replaces the token with *** when git fails."""
    namespace = {"BRANCH": "main"}
    helper = cell_containing(path, "def git(").split("\nfrom ")[0]  # the helper, without platform imports
    exec(helper, namespace)  # noqa: S102 - running the notebook's own cell is the point of the test
    with pytest.raises(RuntimeError) as error:
        namespace["git"]("-C", "/nonexistent-dir-for-test", "fetch", "https://x:SECRET123@example.invalid/r.git",
                         token="SECRET123")
    assert "SECRET123" not in str(error.value)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_run_cell_runs_a_dry_smoke_run(path: Path, tmp_path: Path, capsys):
    """The settings and run cells, executed as they are, launch the toy run to the end."""
    pytest.importorskip("sklearn")
    namespace = {}
    exec(cell_containing(path, "# Settings"), namespace)  # noqa: S102
    namespace.update({"SMOKE": True, "DRY_RUN": True, "SMOKE_NODES": 2, "CODE": str(ROOT), "SEED": 11,
                      "subprocess": __import__("subprocess"), "sys": __import__("sys")})
    run_cell = cell_containing(path, "scripts/cloud_run.py")
    # Point the run at the test folder and switch off syncing (Drive or Kaggle input do not exist here).
    run_cell = re.sub(r"^RUNS_ROOT = .*$", f'RUNS_ROOT = "{tmp_path}"', run_cell, count=1, flags=re.MULTILINE)
    run_cell = re.sub(r"^SYNC = .*$", "SYNC = []", run_cell, count=1, flags=re.MULTILINE)
    exec(run_cell, namespace)  # noqa: S102
    out = capsys.readouterr().out
    assert "smoke_dry_seed11: done" in out and "exit code 0" in out
    assert (tmp_path / "smoke_dry_seed11" / "machine.jsonl").exists()
