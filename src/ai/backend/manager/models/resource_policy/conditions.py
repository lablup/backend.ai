"""Query conditions for resource policy rows."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_int_conditions, make_string_in_factory
from ai.backend.manager.repositories.base import QueryCondition

from .row import KeyPairResourcePolicyRow, ProjectResourcePolicyRow, UserResourcePolicyRow


class KeypairResourcePolicyConditions:
    """Query conditions for filtering keypair resource policies."""

    # ==================== Name Filters ====================

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

    by_name_in = staticmethod(make_string_in_factory(KeyPairResourcePolicyRow.name))

    # ==================== DateTime Filters ====================

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairResourcePolicyRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairResourcePolicyRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairResourcePolicyRow.created_at == dt

        return inner

    # ==================== Int Filters ====================

    by_max_session_lifetime = make_int_conditions(KeyPairResourcePolicyRow.max_session_lifetime)
    by_max_concurrent_sessions = make_int_conditions(
        KeyPairResourcePolicyRow.max_concurrent_sessions
    )
    by_max_containers_per_session = make_int_conditions(
        KeyPairResourcePolicyRow.max_containers_per_session
    )
    by_idle_timeout = make_int_conditions(KeyPairResourcePolicyRow.idle_timeout)
    by_max_concurrent_sftp_sessions = make_int_conditions(
        KeyPairResourcePolicyRow.max_concurrent_sftp_sessions
    )
    by_max_pending_session_count = make_int_conditions(
        KeyPairResourcePolicyRow.max_pending_session_count
    )

    # ==================== Cursor Conditions ====================

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

    # ==================== Name Filters ====================

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

    by_name_in = staticmethod(make_string_in_factory(UserResourcePolicyRow.name))

    # ==================== DateTime Filters ====================

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserResourcePolicyRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserResourcePolicyRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserResourcePolicyRow.created_at == dt

        return inner

    # ==================== Int Filters ====================

    by_max_vfolder_count = make_int_conditions(UserResourcePolicyRow.max_vfolder_count)
    by_max_concurrent_logins = make_int_conditions(UserResourcePolicyRow.max_concurrent_logins)
    by_max_quota_scope_size = make_int_conditions(UserResourcePolicyRow.max_quota_scope_size)
    by_max_session_count_per_model_session = make_int_conditions(
        UserResourcePolicyRow.max_session_count_per_model_session
    )
    by_max_customized_image_count = make_int_conditions(
        UserResourcePolicyRow.max_customized_image_count
    )

    # ==================== Cursor Conditions ====================

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

    # ==================== Name Filters ====================

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

    by_name_in = staticmethod(make_string_in_factory(ProjectResourcePolicyRow.name))

    # ==================== DateTime Filters ====================

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectResourcePolicyRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectResourcePolicyRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectResourcePolicyRow.created_at == dt

        return inner

    # ==================== Int Filters ====================

    by_max_vfolder_count = make_int_conditions(ProjectResourcePolicyRow.max_vfolder_count)
    by_max_quota_scope_size = make_int_conditions(ProjectResourcePolicyRow.max_quota_scope_size)
    by_max_network_count = make_int_conditions(ProjectResourcePolicyRow.max_network_count)

    # ==================== Cursor Conditions ====================

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
