import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation
from flake8_bai.rules.dataclass_decorator import DataclassDecorator


class DataFrozenRule(Rule):
    """BAI101: a dataclass under `manager/data` is `@dataclass(frozen=True)`."""

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/manager/data")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            decorator = DataclassDecorator(node)
            if decorator.present and not decorator.frozen:
                yield Violation(node.lineno, node.col_offset, BAICode.DATA_NOT_FROZEN)
