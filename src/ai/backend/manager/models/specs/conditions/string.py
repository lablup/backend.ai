"""String conditions on one column."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringInMatchSpec, StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn


class StringEqualityConditions:
    """Equality and membership on one string column.

    Declared for a column no index can serve a partial match on: ``sa.Text``, or a
    length above 1024.
    """

    _column: FilterColumn

    def __init__(self, column: FilterColumn) -> None:
        self._column = column

    def equals(self, spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(self._column) == spec.value.lower()
            else:
                condition = self._column == spec.value
            return self._finish(condition, spec.negated)

        return inner

    def in_(self, spec: StringInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(self._column).in_([v.lower() for v in spec.values])
            else:
                condition = self._column.in_(spec.values)
            return self._finish(condition, spec.negated)

        return inner

    def _finish(
        self, condition: sa.sql.expression.ColumnElement[bool], negated: bool
    ) -> sa.sql.expression.ColumnElement[bool]:
        if negated:
            return sa.not_(condition)
        return condition


class StringConditions(StringEqualityConditions):
    """String match operations on one column.

    A column mapped through a ``TypeDecorator`` over ``VARCHAR`` is passed as
    ``sa.type_coerce(col, sa.String())``.
    """

    def contains(self, spec: StringMatchSpec) -> QueryCondition:
        return self._like(f"%{spec.value}%", spec)

    def starts_with(self, spec: StringMatchSpec) -> QueryCondition:
        return self._like(f"{spec.value}%", spec)

    def ends_with(self, spec: StringMatchSpec) -> QueryCondition:
        return self._like(f"%{spec.value}", spec)

    def _like(self, pattern: str, spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = self._column.ilike(pattern)
            else:
                condition = self._column.like(pattern)
            return self._finish(condition, spec.negated)

        return inner
