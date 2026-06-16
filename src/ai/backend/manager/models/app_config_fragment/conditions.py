"""Query conditions for the app_config_fragment domain."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.repositories.base import QueryCondition


class AppConfigFragmentConditions:
    """QueryCondition factories for app-config fragment filtering."""

    @staticmethod
    def by_ids(fragment_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return AppConfigFragmentRow.id.in_(fragment_ids)

        return inner

    @staticmethod
    def by_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            condition = AppConfigFragmentRow.id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            condition = AppConfigFragmentRow.id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigFragmentRow.name.ilike(f"%{spec.value}%")
            else:
                condition = AppConfigFragmentRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AppConfigFragmentRow.name) == spec.value.lower()
            else:
                condition = AppConfigFragmentRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigFragmentRow.name.ilike(f"{spec.value}%")
            else:
                condition = AppConfigFragmentRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigFragmentRow.name.ilike(f"%{spec.value}")
            else:
                condition = AppConfigFragmentRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(AppConfigFragmentRow.name))

    @staticmethod
    def by_scope_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigFragmentRow.scope_id.ilike(f"%{spec.value}%")
            else:
                condition = AppConfigFragmentRow.scope_id.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AppConfigFragmentRow.scope_id) == spec.value.lower()
            else:
                condition = AppConfigFragmentRow.scope_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigFragmentRow.scope_id.ilike(f"{spec.value}%")
            else:
                condition = AppConfigFragmentRow.scope_id.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigFragmentRow.scope_id.ilike(f"%{spec.value}")
            else:
                condition = AppConfigFragmentRow.scope_id.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_scope_id_in = staticmethod(make_string_in_factory(AppConfigFragmentRow.scope_id))

    @staticmethod
    def by_scope_type_equals(scope_type: str) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return AppConfigFragmentRow.scope_type == scope_type

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(AppConfigFragmentRow.created_at)
                .where(AppConfigFragmentRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return AppConfigFragmentRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(AppConfigFragmentRow.created_at)
                .where(AppConfigFragmentRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return AppConfigFragmentRow.created_at > subquery

        return inner
