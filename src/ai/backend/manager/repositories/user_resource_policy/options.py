from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = ("UserResourcePolicyConditions", "UserResourcePolicyOrders")


class UserResourcePolicyConditions:
    """Query conditions for user resource policies."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserResourcePolicyRow.name.ilike(f"%{spec.value}%")
            else:
                condition = UserResourcePolicyRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserResourcePolicyRow.name) == spec.value.lower()
            else:
                condition = UserResourcePolicyRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserResourcePolicyRow.name.ilike(f"{spec.value}%")
            else:
                condition = UserResourcePolicyRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserResourcePolicyRow.name.ilike(f"%{spec.value}")
            else:
                condition = UserResourcePolicyRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class UserResourcePolicyOrders:
    """Query orders for user resource policies."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.name.asc()
        return UserResourcePolicyRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserResourcePolicyRow.created_at.asc()
        return UserResourcePolicyRow.created_at.desc()
