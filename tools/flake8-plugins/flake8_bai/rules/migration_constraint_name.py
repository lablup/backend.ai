import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class ConstraintNameConvention:
    """Names the naming convention of `manager/models/base.py` gives a constraint."""

    def foreign_key(self, table: str, column: str, referred_table: str) -> str:
        return f"fk_{table}_{column}_{referred_table}"

    def unique(self, table: str, column: str) -> str:
        return f"uq_{table}_{column}"

    def index(self, table: str, column: str) -> str:
        return f"ix_{table}_{column}"

    def primary_key(self, table: str) -> str:
        return f"pk_{table}"

    def is_check(self, table: str, name: str) -> bool:
        return name.startswith(f"ck_{table}_")


class MigrationConstraintNameRule(Rule):
    """BAI303: an unreleased migration wraps a constraint name the convention gives in `op.f()`.

    Checks the `op.create_*` constraint and index calls and the constraints inside `op.create_table`.
    """

    _unreleased_marker = "# Part of: NEXT_RELEASE_VERSION"

    _convention: ConstraintNameConvention

    def __init__(self, path: SourcePath) -> None:
        super().__init__(path)
        self._convention = ConstraintNameConvention()

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/manager/models/alembic/versions") and path.contains(
            self._unreleased_marker
        )

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            operation = self._op_name(node)
            if operation == "create_table":
                yield from self._check_table(node)
            elif operation is not None:
                name = self._string(self._arg(node, 0, self._name_keyword(operation)))
                if name is not None and self._is_convention_name(operation, node, name):
                    yield Violation(node.lineno, node.col_offset, BAICode.MIGRATION_CONSTRAINT_NAME)

    def _check_table(self, call: ast.Call) -> Iterator[Violation]:
        table = self._string(self._arg(call, 0, "table_name"))
        if table is None:
            return
        for node in call.args[1:]:
            if not isinstance(node, ast.Call):
                continue
            if self._call_name(node) == "Column":
                yield from self._check_column(table, node)
                continue
            name = self._string(self._keyword(node, "name"))
            if name is not None and self._is_table_convention_name(table, node, name):
                yield Violation(node.lineno, node.col_offset, BAICode.MIGRATION_CONSTRAINT_NAME)

    def _check_column(self, table: str, column: ast.Call) -> Iterator[Violation]:
        column_name = self._string(column.args[0]) if column.args else None
        for node in column.args[1:]:
            if not isinstance(node, ast.Call) or self._call_name(node) != "ForeignKey":
                continue
            name = self._string(self._keyword(node, "name"))
            referred = self._referred_table(self._string(self._arg(node, 0, "column")))
            if name is None or column_name is None or referred is None:
                continue
            if name == self._convention.foreign_key(table, column_name, referred):
                yield Violation(node.lineno, node.col_offset, BAICode.MIGRATION_CONSTRAINT_NAME)

    def _is_convention_name(self, operation: str, call: ast.Call, name: str) -> bool:
        table = self._string(
            self._arg(
                call, 1, "source_table" if operation == "create_foreign_key" else "table_name"
            )
        )
        if table is None:
            return False
        match operation:
            case "create_foreign_key":
                referred = self._string(self._arg(call, 2, "referent_table"))
                column = self._first_string(self._arg(call, 3, "local_cols"))
                if referred is None or column is None:
                    return False
                return name == self._convention.foreign_key(table, column, referred)
            case "create_unique_constraint":
                column = self._first_string(self._arg(call, 2, "columns"))
                return column is not None and name == self._convention.unique(table, column)
            case "create_index":
                column = self._first_string(self._arg(call, 2, "columns"))
                return column is not None and name == self._convention.index(table, column)
            case "create_primary_key":
                return name == self._convention.primary_key(table)
            case "create_check_constraint":
                return self._convention.is_check(table, name)
        return False

    def _is_table_convention_name(self, table: str, constraint: ast.Call, name: str) -> bool:
        match self._call_name(constraint):
            case "ForeignKeyConstraint":
                column = self._first_string(self._arg(constraint, 0, "columns"))
                referred = self._referred_table(
                    self._first_string(self._arg(constraint, 1, "refcolumns"))
                )
                if column is None or referred is None:
                    return False
                return name == self._convention.foreign_key(table, column, referred)
            case "UniqueConstraint":
                column = self._string(constraint.args[0]) if constraint.args else None
                return column is not None and name == self._convention.unique(table, column)
            case "PrimaryKeyConstraint":
                return name == self._convention.primary_key(table)
            case "CheckConstraint":
                return self._convention.is_check(table, name)
        return False

    def _referred_table(self, column: str | None) -> str | None:
        if column is None or "." not in column:
            return None
        return column.rsplit(".", 1)[0].rsplit(".", 1)[-1]

    def _op_name(self, call: ast.Call) -> str | None:
        func = call.func
        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "op"
        ):
            return None
        if func.attr in (
            "create_table",
            "create_foreign_key",
            "create_unique_constraint",
            "create_index",
            "create_primary_key",
            "create_check_constraint",
        ):
            return func.attr
        return None

    def _name_keyword(self, operation: str) -> str:
        return "index_name" if operation == "create_index" else "constraint_name"

    def _call_name(self, call: ast.Call) -> str | None:
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        if isinstance(call.func, ast.Name):
            return call.func.id
        return None

    def _arg(self, call: ast.Call, position: int, keyword: str) -> ast.expr | None:
        value = self._keyword(call, keyword)
        if value is not None:
            return value
        return call.args[position] if len(call.args) > position else None

    def _keyword(self, call: ast.Call, keyword: str) -> ast.expr | None:
        for item in call.keywords:
            if item.arg == keyword:
                return item.value
        return None

    def _string(self, node: ast.expr | None) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _first_string(self, node: ast.expr | None) -> str | None:
        if isinstance(node, (ast.List, ast.Tuple)) and node.elts:
            return self._string(node.elts[0])
        return None
