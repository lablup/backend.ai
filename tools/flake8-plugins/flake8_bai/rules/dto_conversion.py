import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class DtoConversionRule(Rule):
    """BAI203: a class under `common/dto/manager/v2` has no `to_*` or `from_*` method."""

    _prefixes = ("to_", "from_")

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/common/dto/manager/v2")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(
                    item, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and item.name.startswith(self._prefixes):
                    yield Violation(item.lineno, item.col_offset, BAICode.DTO_CONVERSION)
