import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class AdminResolverCheckRule(Rule):
    """BAI402: a decorated `admin_*` resolver under `manager/api/gql` calls `check_admin_only()` first.

    A docstring before the call is allowed.
    """

    _check_name = "check_admin_only"

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/manager/api/gql")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("admin_") or not node.decorator_list:
                continue
            if not self._starts_with_check(node.body):
                yield Violation(node.lineno, node.col_offset, BAICode.ADMIN_RESOLVER_CHECK)

    def _starts_with_check(self, body: list[ast.stmt]) -> bool:
        statements = body
        match statements:
            case [ast.Expr(value=ast.Constant(value=str())), *rest]:
                statements = rest
        if not statements:
            return False
        match statements[0]:
            case ast.Expr(value=ast.Call(func=ast.Name(id=name) | ast.Attribute(attr=name))):
                return name == self._check_name
        return False
