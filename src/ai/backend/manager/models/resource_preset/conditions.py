"""Query conditions for resource preset rows."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.repositories.base import QueryCondition

__all__ = ("ResourcePresetConditions",)


class ResourcePresetConditions:
    """Query conditions for resource presets."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourcePresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ResourcePresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourcePresetRow.name) == spec.value.lower()
            else:
                condition = ResourcePresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourcePresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = ResourcePresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourcePresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = ResourcePresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourcePresetRow.scaling_group_name.ilike(f"%{spec.value}%")
            else:
                condition = ResourcePresetRow.scaling_group_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = (
                    sa.func.lower(ResourcePresetRow.scaling_group_name) == spec.value.lower()
                )
            else:
                condition = ResourcePresetRow.scaling_group_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourcePresetRow.scaling_group_name.ilike(f"{spec.value}%")
            else:
                condition = ResourcePresetRow.scaling_group_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourcePresetRow.scaling_group_name.ilike(f"%{spec.value}")
            else:
                condition = ResourcePresetRow.scaling_group_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourcePresetRow.id < sa.text(f"'{cursor_id}'::uuid")

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourcePresetRow.id > sa.text(f"'{cursor_id}'::uuid")

        return inner
