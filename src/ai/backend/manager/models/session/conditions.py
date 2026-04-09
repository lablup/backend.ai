"""Query conditions for session rows."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa

if TYPE_CHECKING:
    from ai.backend.common.data.filter_specs import (
        StringMatchSpec,
        UUIDEqualMatchSpec,
        UUIDInMatchSpec,
    )

from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import KernelMatchType, SessionStatus
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.repositories.base import QueryCondition

from .row import SessionRow


class SessionConditions:
    """Query conditions for sessions."""

    @staticmethod
    def by_ids(session_ids: Collection[SessionId]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.id.in_(session_ids)

        return inner

    @staticmethod
    def by_statuses(statuses: Collection[SessionStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_scaling_group(scaling_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.scaling_group_name == scaling_group

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.name.ilike(f"%{spec.value}%")
            else:
                condition = SessionRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(SessionRow.name) == spec.value.lower()
            else:
                condition = SessionRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.name.ilike(f"{spec.value}%")
            else:
                condition = SessionRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.name.ilike(f"%{spec.value}")
            else:
                condition = SessionRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(SessionRow.name))

    @staticmethod
    def by_access_key_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.access_key.ilike(f"%{spec.value}%")
            else:
                condition = SessionRow.access_key.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(SessionRow.access_key) == spec.value.lower()
            else:
                condition = SessionRow.access_key == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.access_key.ilike(f"{spec.value}%")
            else:
                condition = SessionRow.access_key.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.access_key.ilike(f"%{spec.value}")
            else:
                condition = SessionRow.access_key.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_access_key_in = staticmethod(make_string_in_factory(SessionRow.access_key))

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = SessionRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(SessionRow.domain_name) == spec.value.lower()
            else:
                condition = SessionRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = SessionRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = SessionRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_domain_name_in = staticmethod(make_string_in_factory(SessionRow.domain_name))
    by_scaling_group_in = staticmethod(make_string_in_factory(SessionRow.scaling_group_name))

    @staticmethod
    def by_scaling_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.scaling_group_name.ilike(f"%{spec.value}%")
            else:
                condition = SessionRow.scaling_group_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scaling_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(SessionRow.scaling_group_name) == spec.value.lower()
            else:
                condition = SessionRow.scaling_group_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scaling_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.scaling_group_name.ilike(f"{spec.value}%")
            else:
                condition = SessionRow.scaling_group_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scaling_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = SessionRow.scaling_group_name.ilike(f"%{spec.value}")
            else:
                condition = SessionRow.scaling_group_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # Promotion handler conditions - optimized with EXISTS subqueries
    # These check kernel status conditions without loading kernel data

    @staticmethod
    def all_kernels_in_statuses(statuses: Collection[KernelStatus]) -> QueryCondition:
        """Filter sessions where ALL kernels are in the specified statuses.

        Uses NOT EXISTS to check that no kernel is outside the specified statuses.
        Also requires at least one kernel exists (sessions without kernels are excluded).
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            # Subquery: check if any kernel is NOT in the specified statuses
            kernel_not_in_statuses = (
                sa.select(sa.literal(1))
                .select_from(KernelRow)
                .where(
                    KernelRow.session_id == SessionRow.id,
                    KernelRow.status.notin_(statuses),
                )
                .exists()
            )
            # Subquery: check if session has at least one kernel
            has_kernels = (
                sa.select(sa.literal(1))
                .select_from(KernelRow)
                .where(KernelRow.session_id == SessionRow.id)
                .exists()
            )
            # ALL: no kernel outside statuses AND has at least one kernel
            return sa.and_(~kernel_not_in_statuses, has_kernels)

        return inner

    @staticmethod
    def any_kernel_in_statuses(statuses: Collection[KernelStatus]) -> QueryCondition:
        """Filter sessions where at least one kernel is in the specified statuses.

        Uses EXISTS to check that at least one kernel is in the specified statuses.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            # Subquery: check if any kernel is in the specified statuses
            return (
                sa.select(sa.literal(1))
                .select_from(KernelRow)
                .where(
                    KernelRow.session_id == SessionRow.id,
                    KernelRow.status.in_(statuses),
                )
                .exists()
            )

        return inner

    @staticmethod
    def no_kernel_in_statuses(statuses: Collection[KernelStatus]) -> QueryCondition:
        """Filter sessions where no kernel is in the specified statuses.

        Uses NOT EXISTS to check that no kernel is in the specified statuses.
        Also requires at least one kernel exists (sessions without kernels are excluded).
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            # Subquery: check if any kernel is in the specified statuses
            kernel_in_statuses = (
                sa.select(sa.literal(1))
                .select_from(KernelRow)
                .where(
                    KernelRow.session_id == SessionRow.id,
                    KernelRow.status.in_(statuses),
                )
                .exists()
            )
            # Subquery: check if session has at least one kernel
            has_kernels = (
                sa.select(sa.literal(1))
                .select_from(KernelRow)
                .where(KernelRow.session_id == SessionRow.id)
                .exists()
            )
            # NOT_ANY: no kernel in statuses AND has at least one kernel
            return sa.and_(~kernel_in_statuses, has_kernels)

        return inner

    @staticmethod
    def by_kernel_match(
        statuses: Collection[KernelStatus],
        match_type: KernelMatchType,
    ) -> QueryCondition:
        """Filter sessions by kernel status match type.

        Args:
            statuses: Kernel statuses to check against
            match_type: How to match kernel statuses (ALL/ANY/NOT_ANY)

        Returns:
            QueryCondition for the specified match type
        """
        match match_type:
            case KernelMatchType.ALL:
                return SessionConditions.all_kernels_in_statuses(statuses)
            case KernelMatchType.ANY:
                return SessionConditions.any_kernel_in_statuses(statuses)
            case KernelMatchType.NOT_ANY:
                return SessionConditions.no_kernel_in_statuses(statuses)

    @staticmethod
    def by_id_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Factory for id equality filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionRow.id != SessionId(spec.value)
            return SessionRow.id == SessionId(spec.value)

        return inner

    @staticmethod
    def by_id_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Factory for id IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            session_ids = [SessionId(v) for v in spec.values]
            if spec.negated:
                return SessionRow.id.notin_(session_ids)
            return SessionRow.id.in_(session_ids)

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[SessionStatus]) -> QueryCondition:
        """Factory for status IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[SessionStatus]) -> QueryCondition:
        """Factory for status NOT IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.status.notin_(statuses)

        return inner

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        """Factory for created_at < dt filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        """Factory for created_at > dt filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        """Factory for created_at == dt filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionRow.created_at == dt

        return inner

    @staticmethod
    def by_user_uuid_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Factory for user UUID equality filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionRow.user_uuid != spec.value
            return SessionRow.user_uuid == spec.value

        return inner

    @staticmethod
    def by_user_uuid_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Factory for user UUID IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionRow.user_uuid.notin_(spec.values)
            return SessionRow.user_uuid.in_(spec.values)

        return inner

    @staticmethod
    def by_group_id_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Factory for group (project) ID equality filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionRow.group_id != spec.value
            return SessionRow.group_id == spec.value

        return inner

    @staticmethod
    def by_group_id_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Factory for group (project) ID IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionRow.group_id.notin_(spec.values)
            return SessionRow.group_id.in_(spec.values)

        return inner

    @staticmethod
    def by_agent_id(agent_id: str) -> QueryCondition:
        """Filter sessions that have kernels running on the given agent."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.literal(agent_id) == sa.any_(SessionRow.agent_ids)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(SessionRow.created_at).where(SessionRow.id == cursor_id).scalar_subquery()
            )
            return SessionRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(SessionRow.created_at).where(SessionRow.id == cursor_id).scalar_subquery()
            )
            return SessionRow.created_at > subquery

        return inner
