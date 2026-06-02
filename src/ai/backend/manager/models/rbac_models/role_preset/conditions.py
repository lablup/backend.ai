"""Query conditions for role preset rows."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import QueryCondition

__all__ = ("RolePresetConditions",)


class RolePresetConditions:
    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RolePresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = RolePresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(RolePresetRow.name) == spec.value.lower()
            else:
                condition = RolePresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RolePresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = RolePresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = RolePresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = RolePresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(RolePresetRow.name))

    @staticmethod
    def by_scope_type(scope_type: ScopeType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePresetRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_auto_assign(auto_assign: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePresetRow.auto_assign == auto_assign

        return inner

    @staticmethod
    def by_deleted(deleted: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePresetRow.deleted == deleted

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePresetRow.id < sa.text(f"'{cursor_id}'::uuid")

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePresetRow.id > sa.text(f"'{cursor_id}'::uuid")

        return inner
