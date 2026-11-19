import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation
from flake8_bai.rules.dataclass_decorator import DataclassDecorator


class DtoDataclassRule(Rule):
    """BAI201: a class under `common/dto` is not a `@dataclass`."""

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/common/dto")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and DataclassDecorator(node).present:
                yield Violation(node.lineno, node.col_offset, BAICode.DTO_DATACLASS)
