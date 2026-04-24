"""Query conditions for the app_config_policy domain."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.repositories.base import QueryCondition


class AppConfigPolicyConditions:
    """QueryCondition factories for app-config policy filtering."""

    @staticmethod
    def by_ids(policy_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return AppConfigPolicyRow.id.in_(policy_ids)

        return inner

    @staticmethod
    def by_config_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigPolicyRow.config_name.ilike(f"%{spec.value}%")
            else:
                condition = AppConfigPolicyRow.config_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_config_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(AppConfigPolicyRow.config_name) == spec.value.lower()
            else:
                condition = AppConfigPolicyRow.config_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_config_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigPolicyRow.config_name.ilike(f"{spec.value}%")
            else:
                condition = AppConfigPolicyRow.config_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_config_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = AppConfigPolicyRow.config_name.ilike(f"%{spec.value}")
            else:
                condition = AppConfigPolicyRow.config_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_config_name_in = staticmethod(make_string_in_factory(AppConfigPolicyRow.config_name))

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(AppConfigPolicyRow.created_at)
                .where(AppConfigPolicyRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return AppConfigPolicyRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(AppConfigPolicyRow.created_at)
                .where(AppConfigPolicyRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return AppConfigPolicyRow.created_at > subquery

        return inner
