"""Query conditions for runtime variant preset rows."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base import QueryCondition

__all__ = ("RuntimeVariantPresetConditions",)


class RuntimeVariantPresetConditions:
    @staticmethod
    def by_runtime_variant_id(variant_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantPresetRow.runtime_variant == variant_id

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantPresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = RuntimeVariantPresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(RuntimeVariantPresetRow.name) == spec.value.lower()
            else:
                condition = RuntimeVariantPresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantPresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = RuntimeVariantPresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RuntimeVariantPresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = RuntimeVariantPresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantPresetRow.id < sa.text(f"'{cursor_id}'::uuid")

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RuntimeVariantPresetRow.id > sa.text(f"'{cursor_id}'::uuid")

        return inner
