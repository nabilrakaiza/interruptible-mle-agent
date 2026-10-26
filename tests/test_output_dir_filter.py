"""The controller disables a script's own module-level OUTPUT_DIR assignments."""

# ruff: noqa: S102  (the tests run their own small scripts)

from imle.agents.coding import with_output_dir


def test_semicolon_inside_comment():
    """A semicolon in a comment must not bypass filtering."""
    script = 'OUTPUT_DIR = "output"  # harness; do not redefine\n'

    result = with_output_dir(script, "/output")

    namespace = {}
    exec(result, namespace)

    assert namespace["OUTPUT_DIR"] == "/output"


def test_normal_output_assignment():
    """A normal assignment must also be disabled."""
    script = 'OUTPUT_DIR = "output"\n'

    result = with_output_dir(script, "/output")

    namespace = {}
    exec(result, namespace)

    assert namespace["OUTPUT_DIR"] == "/output"


def test_assignment_after_a_semicolon_is_disabled():
    """`import os; OUTPUT_DIR = ...` keeps the import and drops the assignment (A4-off n2, n6 and C1 n3, 25 Oct)."""
    for line in ['import os; OUTPUT_DIR = os.environ.get("OUTPUT_DIR", ".")',
                 'import os; OUTPUT_DIR = os.environ["OUTPUT_DIR"]',
                 'OUTPUT_DIR = "output"; x = 1']:
        namespace = {}
        exec(with_output_dir(line + "\nimport os\nx = 1\n", "/output"), namespace)
        assert namespace["OUTPUT_DIR"] == "/output" and namespace["x"] == 1


def test_line_numbers_and_unicode_are_kept():
    """Non-ASCII text before the assignment does not shift the cut, and the line count stays the same."""
    script = 'note = "é"; OUTPUT_DIR = (\n    "elsewhere")\nprint(note)\n'
    out = with_output_dir(script, "/output")
    namespace = {}
    exec(out, namespace)
    assert namespace["OUTPUT_DIR"] == "/output" and namespace["note"] == "é"
    assert len(out.splitlines()) == len(script.splitlines()) + 1


def test_original_deepseek_script(tmp_path):
    """The exact failed DeepSeek script must use the controller path."""
    script = '''
import os

OUTPUT_DIR = "output"  # will be set by the harness; do not redefine

os.makedirs(OUTPUT_DIR, exist_ok=True)
'''

    result = with_output_dir(script, str(tmp_path / "out"))

    namespace = {}
    exec(result, namespace)

    assert namespace["OUTPUT_DIR"] == str(tmp_path / "out") and (tmp_path / "out").is_dir()
