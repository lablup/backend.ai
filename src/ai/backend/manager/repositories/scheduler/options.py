"""Query conditions and orders for scheduler sessions, kernels, and users."""

from __future__ import annotations

from collections.abc import Collection
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


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
    def by_agent_ids(agent_ids: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.agent.in_(agent_ids)

        return inner

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
    def by_cursor_forward(cursor: str) -> QueryCondition:
        """Condition for forward pagination (after cursor)."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.id > cursor

        return inner

    @staticmethod
    def by_cursor_backward(cursor: str) -> QueryCondition:
        """Condition for backward pagination (before cursor)."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.id < cursor

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
