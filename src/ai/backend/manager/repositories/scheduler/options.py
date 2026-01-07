"""Query conditions and orders for scheduler sessions and kernels."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
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
    """Query conditions for kernels (used in session-kernel joins)."""

    @staticmethod
    def by_statuses(statuses: Collection[KernelStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.status.in_(statuses)

        return inner


class KernelOrders:
    """Query orders for kernels."""

    @staticmethod
    def cluster_idx(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_idx.asc()
        return KernelRow.cluster_idx.desc()
