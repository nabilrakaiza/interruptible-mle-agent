# Interface requests from role 3

Changes to files role 3 does not own, needed or useful for A1, A4 and C5. None of them blocks the role 3 code: each has a workaround in place, stated below. Nothing here has been sent yet.

## 1. Ruff 0.17 flags `Optional[...]` in the shared contracts (Sahi: `tree.py`, `intervention.py`)

**What.** `ruff check src tests scripts` fails on main with ruff 0.17.2, the version `pip install -e ".[dev]"` installs today: 11 `UP045` errors ("use `X | None`"), all in `tree.py` and `intervention.py`. Ruff 0.17's default rules include `UP045`; older versions did not.

**Why.** `CONTRIBUTING.md` asks for a clean `ruff check` before pushing, and nobody can get one without touching shared contracts.

**Proposed diff.** Either pin the linter (`dev = ["pytest", "ruff<0.17"]` in `pyproject.toml`), or apply `ruff check --fix src/imle/tree.py src/imle/intervention.py`. That changes `Optional[X]` to `X | None`, which needs no behaviour change on Python 3.10+, the project's minimum.

**Workaround.** Role 3's commits are checked with the full `ruff check src tests scripts`, accepting only these 11 pre-existing errors; every role 3 file passes.
