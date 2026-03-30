"""Query conditions for kernel rows."""

from __future__ import annotations

from collections.abc import Collection
from typing import TYPE_CHECKING

import sqlalchemy as sa

if TYPE_CHECKING:
    from ai.backend.common.data.filter_specs import (
        UUIDEqualMatchSpec,
        UUIDInMatchSpec,
    )
    from ai.backend.manager.data.kernel.types import KernelStatusInMatchSpec

from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.repositories.base import QueryCondition

from .row import KernelRow

# Default lookback period for fair share calculation (28 days)
DEFAULT_LOOKBACK_DAYS = 28


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
    def by_agent_id(agent_id: AgentId) -> QueryCondition:
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
