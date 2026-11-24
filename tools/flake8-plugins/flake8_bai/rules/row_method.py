import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class RowMethodRule(Rule):
    """BAI302: a Row class under `manager/models` holds only `to_*`/`from_*` methods and dunders.

    A Row class is one whose name ends in `Row` or that subclasses `Base`. Decorated methods count too.
    """

    _allowed_prefixes = ("to_", "from_")

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/manager/models") and not path.is_under(
            "src/ai/backend/manager/models/alembic"
        )

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not self._is_row_class(node):
                continue
            for method in node.body:
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not self._allowed(method.name):
                    yield Violation(method.lineno, method.col_offset, BAICode.ROW_METHOD)

    def _is_row_class(self, node: ast.ClassDef) -> bool:
        if node.name.endswith("Row"):
            return True
        return any(isinstance(base, ast.Name) and base.id == "Base" for base in node.bases)

    def _allowed(self, name: str) -> bool:
        if name.startswith("__") and name.endswith("__"):
            return True
        return name.startswith(self._allowed_prefixes)
