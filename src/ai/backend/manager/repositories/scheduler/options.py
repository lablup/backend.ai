"""Query conditions and orders for scheduler sessions, kernels, and users."""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.models.scaling_group.row import ScalingGroupRow

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.base import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
    from ai.backend.manager.api.gql.kernel.types import KernelStatusInMatchSpec

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import KernelMatchType, SessionStatus
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

# Default lookback period for fair share calculation (28 days)
DEFAULT_LOOKBACK_DAYS = 28


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


class SessionOrders:
    """Query orders for sessions."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.created_at.asc()
        return SessionRow.created_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.id.asc()
        return SessionRow.id.desc()


class KernelConditions:
    """Query conditions for kernels."""

    @staticmethod
    def by_id(kernel_id: KernelId) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.id == kernel_id

        return inner

    @staticmethod
    def by_ids(kernel_ids: Collection[KernelId]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.id.in_(kernel_ids)

        return inner

    @staticmethod
    def by_id_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Factory for id equality filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return KernelRow.id != KernelId(spec.value)
            return KernelRow.id == KernelId(spec.value)

        return inner

    @staticmethod
    def by_id_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Factory for id IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            kernel_ids = [KernelId(v) for v in spec.values]
            if spec.negated:
                return KernelRow.id.notin_(kernel_ids)
            return KernelRow.id.in_(kernel_ids)

        return inner

    @staticmethod
    def by_session_ids(session_ids: Collection[SessionId]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.session_id.in_(session_ids)

        return inner

    @staticmethod
    def by_session_id_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Factory for session_id equality filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return KernelRow.session_id != SessionId(spec.value)
            return KernelRow.session_id == SessionId(spec.value)

        return inner

    @staticmethod
    def by_session_id_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Factory for session_id IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            session_ids = [SessionId(v) for v in spec.values]
            if spec.negated:
                return KernelRow.session_id.notin_(session_ids)
            return KernelRow.session_id.in_(session_ids)

        return inner

    @staticmethod
    def by_statuses(statuses: Collection[KernelStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_filter_in(spec: KernelStatusInMatchSpec) -> QueryCondition:
        """Factory for status IN filter."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return KernelRow.status.notin_(spec.values)
            return KernelRow.status.in_(spec.values)

        return inner

    @staticmethod
    def by_scaling_group(scaling_group: str) -> QueryCondition:
        """Filter kernels by scaling group."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.scaling_group == scaling_group

        return inner

    @staticmethod
    def by_agent_id(agent_id: str) -> QueryCondition:
        """Filter kernels by agent ID."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.agent == agent_id

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KernelRow.created_at).where(KernelRow.id == cursor_id).scalar_subquery()
            )
            return KernelRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KernelRow.created_at).where(KernelRow.id == cursor_id).scalar_subquery()
            )
            return KernelRow.created_at > subquery

        return inner

    @staticmethod
    def for_fair_share_observation(
        scaling_group: str,
    ) -> QueryCondition:
        """Filter kernels that need fair share observation.

        Includes:
        1. Running kernels (terminated_at IS NULL) with starts_at set
        2. Recently terminated kernels with unobserved periods
           (terminated_at > last_observed_at, within lookback window)

        The lookback_days is fetched from scaling_groups.fair_share_spec via subquery.

        Args:
            scaling_group: The scaling group to filter

        Returns:
            QueryCondition for fair share observation targets
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            # Subquery to get lookback_days from scaling_group's fair_share_spec
            # Falls back to DEFAULT_LOOKBACK_DAYS if not set
            lookback_days_subquery = (
                sa.select(
                    sa.func.coalesce(
                        sa.cast(
                            ScalingGroupRow.fair_share_spec["lookback_days"].as_string(),
                            sa.Integer,
                        ),
                        DEFAULT_LOOKBACK_DAYS,
                    )
                )
                .where(ScalingGroupRow.name == scaling_group)
                .scalar_subquery()
            )

            # Calculate lookback cutoff using the subquery
            lookback_cutoff = sa.func.now() - sa.func.make_interval(0, 0, 0, lookback_days_subquery)

            return sa.and_(
                KernelRow.scaling_group == scaling_group,
                KernelRow.starts_at.isnot(None),  # Must have started
                sa.or_(
                    # Running kernels (not yet terminated)
                    KernelRow.terminated_at.is_(None),
                    # Terminated kernels with unobserved period, within lookback
                    sa.and_(
                        KernelRow.terminated_at
                        > sa.func.coalesce(
                            KernelRow.last_observed_at,
                            KernelRow.starts_at,
                        ),
                        KernelRow.terminated_at >= lookback_cutoff,
                    ),
                ),
            )

        return inner


class KernelOrders:
    """Query orders for kernels."""

    @staticmethod
    def cluster_idx(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_idx.asc()
        return KernelRow.cluster_idx.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.created_at.asc()
        return KernelRow.created_at.desc()

    @staticmethod
    def terminated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.terminated_at.asc()
        return KernelRow.terminated_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.status.asc()
        return KernelRow.status.desc()

    @staticmethod
    def cluster_mode(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_mode.asc()
        return KernelRow.cluster_mode.desc()

    @staticmethod
    def cluster_hostname(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_hostname.asc()
        return KernelRow.cluster_hostname.desc()


class UserConditions:
    """Query conditions for users."""

    @staticmethod
    def by_uuids(user_uuids: Collection[UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.uuid.in_(user_uuids)

        return inner


class ImageConditions:
    """Query conditions for images."""

    @staticmethod
    def by_identifiers(identifiers: Collection[tuple[str, str]]) -> QueryCondition:
        """Filter images by list of (canonical, architecture) tuples.

        Args:
            identifiers: Collection of (canonical, architecture) tuples

        Returns:
            QueryCondition that matches any of the identifiers
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if not identifiers:
                return sa.literal(False)

            conditions = [
                sa.and_(
                    ImageRow.name == canonical,
                    ImageRow.architecture == architecture,
                )
                for canonical, architecture in identifiers
            ]
            return sa.or_(*conditions)

        return inner
