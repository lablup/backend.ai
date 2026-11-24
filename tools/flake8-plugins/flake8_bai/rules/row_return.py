import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class RowReturnRule(Rule):
    """BAI301: a public method of a class in `repository.py` or `repositories.py` returns no Row.

    A Row is a name ending in `Row`, also inside a generic or a union; `Row` itself is SQLAlchemy's.
    """

    _file_names = frozenset({"repository.py", "repositories.py"})

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.name in self._file_names and path.is_under(
            "src/ai/backend/manager/repositories"
        )

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for method in node.body:
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if method.name.startswith("_") or method.returns is None:
                    continue
                if self._names_row(method.returns):
                    yield Violation(method.lineno, method.col_offset, BAICode.ROW_RETURN)

    def _names_row(self, annotation: ast.expr) -> bool:
        for node in ast.walk(annotation):
            if isinstance(node, ast.Name) and self._is_row(node.id):
                return True
            if isinstance(node, ast.Attribute) and self._is_row(node.attr):
                return True
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                try:
                    parsed = ast.parse(node.value, mode="eval")
                except SyntaxError:
                    continue
                if self._names_row(parsed.body):
                    return True
        return False

    def _is_row(self, name: str) -> bool:
        return name.endswith("Row") and name != "Row"
