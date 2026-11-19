import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class AppProxyNativeEnumRule(Rule):
    """BAI404: an App Proxy column type is not a native ENUM.

    Checks the arguments of `mapped_column()` and `Column()` for `EnumType`, `ENUM` and SQLAlchemy `Enum`.
    """

    _column_factories = frozenset({"mapped_column", "Column"})
    _native_enum_types = frozenset({"EnumType", "ENUM"})
    _sqlalchemy_modules = frozenset({"sa", "sqlalchemy"})

    _sqlalchemy_enum_aliases: set[str]

    def __init__(self, path: SourcePath) -> None:
        super().__init__(path)
        self._sqlalchemy_enum_aliases = set()

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/appproxy")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        self._sqlalchemy_enum_aliases = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy"
            for alias in node.names
            if alias.name == "Enum"
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or self._callee(node) not in self._column_factories:
                continue
            for argument in [*node.args, *(k.value for k in node.keywords)]:
                for inner in ast.walk(argument):
                    if isinstance(inner, ast.Call) and self._is_native_enum(inner):
                        yield Violation(
                            inner.lineno, inner.col_offset, BAICode.APPPROXY_NATIVE_ENUM
                        )

    def _callee(self, call: ast.Call) -> str | None:
        match call.func:
            case ast.Name(id=name) | ast.Attribute(attr=name):
                return name
        return None

    def _is_native_enum(self, call: ast.Call) -> bool:
        match call.func:
            case ast.Name(id=name):
                return name in self._native_enum_types or name in self._sqlalchemy_enum_aliases
            case ast.Attribute(attr="Enum", value=ast.Name(id=module)):
                return module in self._sqlalchemy_modules
            case ast.Attribute(attr=name):
                return name in self._native_enum_types
        return False
