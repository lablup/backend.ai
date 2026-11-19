import ast
import textwrap
from collections.abc import Callable

import pytest
from flake8_bai.plugin import Plugin


@pytest.fixture
def lint() -> Callable[[str, str], list[tuple[int, str]]]:
    """Run the plugin on `source` as `filename`; return `(line, code)` per violation."""

    def run(filename: str, source: str) -> list[tuple[int, str]]:
        tree = ast.parse(textwrap.dedent(source))
        return [(line, message.split()[0]) for line, _, message, _ in Plugin(tree, filename).run()]

    return run
