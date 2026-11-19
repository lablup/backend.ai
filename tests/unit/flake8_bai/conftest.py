import ast
import textwrap
from typing import Protocol

import pytest
from flake8_bai.plugin import Plugin


class Lint(Protocol):
    def __call__(self, filename: str, source: str) -> list[tuple[int, str]]: ...


@pytest.fixture
def lint() -> Lint:
    """Run the plugin on `source` as `filename`; return `(line, code)` per violation."""

    def run(filename: str, source: str) -> list[tuple[int, str]]:
        tree = ast.parse(textwrap.dedent(source))
        return [(line, message.split()[0]) for line, _, message, _ in Plugin(tree, filename).run()]

    return run
