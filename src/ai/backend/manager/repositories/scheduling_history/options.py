from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

# ========== Session Scheduling History ==========


class SessionSchedulingHistoryConditions:
    """Query conditions for session scheduling history."""

    @staticmethod
    def by_session_id(session_id: SessionId) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.session_id == session_id

        return inner

    @staticmethod
    def by_result(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.result == str(result)

        return inner

    @staticmethod
    def by_from_status(status: SessionStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.from_status == str(status)

        return inner

    @staticmethod
    def by_to_status(status: SessionStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.to_status == str(status)

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.error_code == error_code

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(SessionSchedulingHistoryRow.created_at)
                .where(SessionSchedulingHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return SessionSchedulingHistoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(SessionSchedulingHistoryRow.created_at)
                .where(SessionSchedulingHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return SessionSchedulingHistoryRow.created_at > subquery

        return inner


class SessionSchedulingHistoryOrders:
    """Query orders for session scheduling history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionSchedulingHistoryRow.created_at.asc()
        else:
            return SessionSchedulingHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionSchedulingHistoryRow.updated_at.asc()
        else:
            return SessionSchedulingHistoryRow.updated_at.desc()


# ========== Kernel Scheduling History ==========


class KernelSchedulingHistoryConditions:
    """Query conditions for kernel scheduling history."""

    @staticmethod
    def by_kernel_id(kernel_id: KernelId) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelSchedulingHistoryRow.kernel_id == kernel_id

        return inner

    @staticmethod
    def by_session_id(session_id: SessionId) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelSchedulingHistoryRow.session_id == session_id

        return inner

    @staticmethod
    def by_result(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelSchedulingHistoryRow.result == str(result)

        return inner

    @staticmethod
    def by_from_phase(phase: KernelSchedulingPhase) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelSchedulingHistoryRow.from_phase == str(phase)

        return inner

    @staticmethod
    def by_to_phase(phase: KernelSchedulingPhase) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelSchedulingHistoryRow.to_phase == str(phase)

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelSchedulingHistoryRow.error_code == error_code

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KernelSchedulingHistoryRow.created_at)
                .where(KernelSchedulingHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return KernelSchedulingHistoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KernelSchedulingHistoryRow.created_at)
                .where(KernelSchedulingHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return KernelSchedulingHistoryRow.created_at > subquery

        return inner


class KernelSchedulingHistoryOrders:
    """Query orders for kernel scheduling history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelSchedulingHistoryRow.created_at.asc()
        else:
            return KernelSchedulingHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelSchedulingHistoryRow.updated_at.asc()
        else:
            return KernelSchedulingHistoryRow.updated_at.desc()


# ========== Deployment History ==========


class DeploymentHistoryConditions:
    """Query conditions for deployment history."""

    @staticmethod
    def by_deployment_id(deployment_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.deployment_id == deployment_id

        return inner

    @staticmethod
    def by_result(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.result == str(result)

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.error_code == error_code

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DeploymentHistoryRow.created_at)
                .where(DeploymentHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DeploymentHistoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DeploymentHistoryRow.created_at)
                .where(DeploymentHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DeploymentHistoryRow.created_at > subquery

        return inner


class DeploymentHistoryOrders:
    """Query orders for deployment history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentHistoryRow.created_at.asc()
        else:
            return DeploymentHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentHistoryRow.updated_at.asc()
        else:
            return DeploymentHistoryRow.updated_at.desc()


# ========== Route History ==========


class RouteHistoryConditions:
    """Query conditions for route history."""

    @staticmethod
    def by_route_id(route_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.route_id == route_id

        return inner

    @staticmethod
    def by_deployment_id(deployment_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.deployment_id == deployment_id

        return inner

    @staticmethod
    def by_result(result: SchedulingResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.result == str(result)

        return inner

    @staticmethod
    def by_from_status(status: RouteStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.from_status == status.value

        return inner

    @staticmethod
    def by_to_status(status: RouteStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.to_status == status.value

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.error_code == error_code

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RouteHistoryRow.created_at)
                .where(RouteHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RouteHistoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RouteHistoryRow.created_at)
                .where(RouteHistoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RouteHistoryRow.created_at > subquery

        return inner


class RouteHistoryOrders:
    """Query orders for route history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RouteHistoryRow.created_at.asc()
        else:
            return RouteHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RouteHistoryRow.updated_at.asc()
        else:
            return RouteHistoryRow.updated_at.desc()
