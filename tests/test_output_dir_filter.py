
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


def test_real_semicolon_preserves_existing_behavior():
    """A multi-statement line is currently left unchanged."""
    script = 'OUTPUT_DIR = "output"; x = 1\n'

    result = with_output_dir(script, "/output")

    assert 'OUTPUT_DIR = "output"; x = 1' in result


def test_original_deepseek_script():
    """The exact failed DeepSeek script must use the controller path."""
    script = '''
import os

OUTPUT_DIR = "output"  # will be set by the harness; do not redefine

os.makedirs(OUTPUT_DIR, exist_ok=True)
'''

    result = with_output_dir(script, "/output")

    namespace = {}
    exec(result, namespace)

    assert namespace["OUTPUT_DIR"] == "/output"
