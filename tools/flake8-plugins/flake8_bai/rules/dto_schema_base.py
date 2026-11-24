import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class DtoSchemaBaseRule(Rule):
    """BAI202: a class under `common/dto/manager/v2` does not inherit `BackendAISchema` directly."""

    _base_name = "BackendAISchema"

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/common/dto/manager/v2")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(self._is_schema(b) for b in node.bases):
                yield Violation(node.lineno, node.col_offset, BAICode.DTO_SCHEMA_BASE)

    def _is_schema(self, base: ast.expr) -> bool:
        match base:
            case ast.Name(id=name) | ast.Attribute(attr=name):
                return name == self._base_name
        return False
