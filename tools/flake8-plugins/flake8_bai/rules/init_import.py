import ast
from collections.abc import Iterator

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class InitImportRule(Rule):
    """BAI001: a manager `__init__.py` holds no import."""

    def applies_to(self, path: SourcePath) -> bool:
        return path.name == "__init__.py" and path.is_under("src/ai/backend/manager")

    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                yield Violation(node.lineno, node.col_offset, BAICode.INIT_IMPORT)
