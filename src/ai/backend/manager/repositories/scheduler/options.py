"""Query conditions and orders for scheduler sessions, kernels, and users."""

from __future__ import annotations

from collections.abc import Collection
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import KernelMatchType, SessionStatus
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
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
    def by_session_ids(session_ids: Collection[SessionId]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.session_id.in_(session_ids)

        return inner

    @staticmethod
    def by_statuses(statuses: Collection[KernelStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_scaling_group(scaling_group: str) -> QueryCondition:
        """Filter kernels by scaling group."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.scaling_group == scaling_group

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
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.id.asc()
        return KernelRow.id.desc()


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
