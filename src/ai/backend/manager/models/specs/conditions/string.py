"""String conditions on one column."""

from __future__ import annotations

from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

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


class DelimitedStringConditions(StringConditions):
    """String match operations on one column holding delimiter-joined values.

    ``equals`` and ``in_`` match one element; the partial matches run on the
    whole column.
    """

    _delimiter: str

    def __init__(self, column: FilterColumn, delimiter: str = ",") -> None:
        super().__init__(column)
        self._delimiter = delimiter

    @override
    def equals(self, spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.literal(spec.value.lower()) == sa.any_(
                    self._elements(sa.func.lower(self._column))
                )
            else:
                condition = sa.literal(spec.value) == sa.any_(self._elements(self._column))
            return self._finish(condition, spec.negated)

        return inner

    @override
    def in_(self, spec: StringInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                values = [v.lower() for v in spec.values]
                elements = self._elements(sa.func.lower(self._column))
            else:
                values = list(spec.values)
                elements = self._elements(self._column)
            condition = elements.bool_op("&&")(
                sa.cast(postgresql.array(values), postgresql.ARRAY(sa.Text()))
            )
            return self._finish(condition, spec.negated)

        return inner

    def _elements(
        self, column: sa.sql.expression.ColumnElement[str]
    ) -> sa.sql.expression.ColumnElement[Any]:
        return sa.func.string_to_array(column, self._delimiter)
