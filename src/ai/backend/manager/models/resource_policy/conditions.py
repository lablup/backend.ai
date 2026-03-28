"""Query conditions for resource policy rows."""

from __future__ import annotations

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.repositories.base import QueryCondition

from .row import KeyPairResourcePolicyRow, ProjectResourcePolicyRow, UserResourcePolicyRow


class KeypairResourcePolicyConditions:
    """Query conditions for filtering keypair resource policies."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = KeyPairResourcePolicyRow.name.ilike(f"%{spec.value}%")
            else:
                cond = KeyPairResourcePolicyRow.name.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(KeyPairResourcePolicyRow.name) == spec.value.lower()
            else:
                cond = KeyPairResourcePolicyRow.name == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = KeyPairResourcePolicyRow.name.ilike(f"{spec.value}%")
            else:
                cond = KeyPairResourcePolicyRow.name.like(f"{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = KeyPairResourcePolicyRow.name.ilike(f"%{spec.value}")
            else:
                cond = KeyPairResourcePolicyRow.name.like(f"%{spec.value}")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_cursor_forward(cursor_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KeyPairResourcePolicyRow.created_at)
                .where(KeyPairResourcePolicyRow.name == cursor_name)
                .scalar_subquery()
            )
            return KeyPairResourcePolicyRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KeyPairResourcePolicyRow.created_at)
                .where(KeyPairResourcePolicyRow.name == cursor_name)
                .scalar_subquery()
            )
            return KeyPairResourcePolicyRow.created_at > subquery

        return inner


class UserResourcePolicyConditions:
    """Query conditions for filtering user resource policies."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = UserResourcePolicyRow.name.ilike(f"%{spec.value}%")
            else:
                cond = UserResourcePolicyRow.name.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(UserResourcePolicyRow.name) == spec.value.lower()
            else:
                cond = UserResourcePolicyRow.name == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = UserResourcePolicyRow.name.ilike(f"{spec.value}%")
            else:
                cond = UserResourcePolicyRow.name.like(f"{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = UserResourcePolicyRow.name.ilike(f"%{spec.value}")
            else:
                cond = UserResourcePolicyRow.name.like(f"%{spec.value}")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_cursor_forward(cursor_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserResourcePolicyRow.created_at)
                .where(UserResourcePolicyRow.name == cursor_name)
                .scalar_subquery()
            )
            return UserResourcePolicyRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserResourcePolicyRow.created_at)
                .where(UserResourcePolicyRow.name == cursor_name)
                .scalar_subquery()
            )
            return UserResourcePolicyRow.created_at > subquery

        return inner


class ProjectResourcePolicyConditions:
    """Query conditions for filtering project resource policies."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = ProjectResourcePolicyRow.name.ilike(f"%{spec.value}%")
            else:
                cond = ProjectResourcePolicyRow.name.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(ProjectResourcePolicyRow.name) == spec.value.lower()
            else:
                cond = ProjectResourcePolicyRow.name == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = ProjectResourcePolicyRow.name.ilike(f"{spec.value}%")
            else:
                cond = ProjectResourcePolicyRow.name.like(f"{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = ProjectResourcePolicyRow.name.ilike(f"%{spec.value}")
            else:
                cond = ProjectResourcePolicyRow.name.like(f"%{spec.value}")
            if spec.negated:
                cond = sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_cursor_forward(cursor_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ProjectResourcePolicyRow.created_at)
                .where(ProjectResourcePolicyRow.name == cursor_name)
                .scalar_subquery()
            )
            return ProjectResourcePolicyRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ProjectResourcePolicyRow.created_at)
                .where(ProjectResourcePolicyRow.name == cursor_name)
                .scalar_subquery()
            )
            return ProjectResourcePolicyRow.created_at > subquery

        return inner
