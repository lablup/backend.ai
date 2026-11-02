"""UUID conditions on one column."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class UUIDConditions:
    """UUID equality and membership on one column."""

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._finish(self._column == spec.value, spec.negated)

        return inner

    def in_(self, spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return self._finish(self._column.in_(spec.values), spec.negated)

        return inner

    def _finish(
        self, condition: sa.sql.expression.ColumnElement[bool], negated: bool
    ) -> sa.sql.expression.ColumnElement[bool]:
        if negated:
            return sa.not_(condition)
        return condition
