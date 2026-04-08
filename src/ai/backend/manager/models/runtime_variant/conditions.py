"""Query conditions for runtime variant rows."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base import QueryCondition

__all__ = ("RuntimeVariantConditions",)


class RuntimeVariantConditions:
    """Query conditions for runtime variants."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantRow.name.ilike(f"%{spec.value}%")
            else:
                condition = RuntimeVariantRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(RuntimeVariantRow.name) == spec.value.lower()
            else:
                condition = RuntimeVariantRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantRow.name.ilike(f"{spec.value}%")
            else:
                condition = RuntimeVariantRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantRow.name.ilike(f"%{spec.value}")
            else:
                condition = RuntimeVariantRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(RuntimeVariantRow.name))

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantRow.id < sa.text(f"'{cursor_id}'::uuid")

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantRow.id > sa.text(f"'{cursor_id}'::uuid")

        return inner
