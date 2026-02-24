from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = ("KeypairResourcePolicyConditions", "KeypairResourcePolicyOrders")


class KeypairResourcePolicyConditions:
    """Query conditions for keypair resource policies."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairResourcePolicyRow.name.ilike(f"%{spec.value}%")
            else:
                condition = KeyPairResourcePolicyRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(KeyPairResourcePolicyRow.name) == spec.value.lower()
            else:
                condition = KeyPairResourcePolicyRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairResourcePolicyRow.name.ilike(f"{spec.value}%")
            else:
                condition = KeyPairResourcePolicyRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = KeyPairResourcePolicyRow.name.ilike(f"%{spec.value}")
            else:
                condition = KeyPairResourcePolicyRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class KeypairResourcePolicyOrders:
    """Query orders for keypair resource policies."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.name.asc()
        return KeyPairResourcePolicyRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairResourcePolicyRow.created_at.asc()
        return KeyPairResourcePolicyRow.created_at.desc()
