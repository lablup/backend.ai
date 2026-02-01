from __future__ import annotations

import uuid
from datetime import datetime
from typing import cast

import sqlalchemy as sa

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.api.gql.base import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
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

    # UUID filter conditions for history id
    @staticmethod
    def by_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionSchedulingHistoryRow.id != spec.value
            return SessionSchedulingHistoryRow.id == spec.value

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionSchedulingHistoryRow.id.notin_(spec.values)
            return SessionSchedulingHistoryRow.id.in_(spec.values)

        return inner

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
    def by_results(results: list[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.result.in_([str(r) for r in results])

        return inner

    @staticmethod
    def by_from_status(status: SessionStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.from_status == str(status)

        return inner

    @staticmethod
    def by_from_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.from_status.in_(statuses)

        return inner

    @staticmethod
    def by_to_status(status: SessionStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.to_status == str(status)

        return inner

    @staticmethod
    def by_to_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.to_status.in_(statuses)

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.error_code == error_code

        return inner

    # UUID filter conditions for session_id
    @staticmethod
    def by_session_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionSchedulingHistoryRow.session_id != spec.value
            return SessionSchedulingHistoryRow.session_id == spec.value

        return inner

    @staticmethod
    def by_session_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return SessionSchedulingHistoryRow.session_id.notin_(spec.values)
            return SessionSchedulingHistoryRow.session_id.in_(spec.values)

        return inner

    # String filter conditions for error_code
    @staticmethod
    def by_error_code_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_error_code_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_error_code_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_error_code_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    # String filter conditions for phase
    @staticmethod
    def by_phase_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], SessionSchedulingHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_phase_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], SessionSchedulingHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_phase_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], SessionSchedulingHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_phase_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], SessionSchedulingHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    # String filter conditions for message
    @staticmethod
    def by_message_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_message_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_message_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_message_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], SessionSchedulingHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

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

    # DateTime filter conditions
    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.created_at == dt

        return inner

    @staticmethod
    def by_updated_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.updated_at < dt

        return inner

    @staticmethod
    def by_updated_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.updated_at > dt

        return inner

    @staticmethod
    def by_updated_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SessionSchedulingHistoryRow.updated_at == dt

        return inner


class SessionSchedulingHistoryOrders:
    """Query orders for session scheduling history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionSchedulingHistoryRow.created_at.asc()
        return SessionSchedulingHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionSchedulingHistoryRow.updated_at.asc()
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
            return cast(sa.sql.expression.ColumnElement[bool], KernelSchedulingHistoryRow.from_phase == str(phase))

        return inner

    @staticmethod
    def by_to_phase(phase: KernelSchedulingPhase) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return cast(sa.sql.expression.ColumnElement[bool], KernelSchedulingHistoryRow.to_phase == str(phase))

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
        return KernelSchedulingHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelSchedulingHistoryRow.updated_at.asc()
        return KernelSchedulingHistoryRow.updated_at.desc()


# ========== Deployment History ==========


class DeploymentHistoryConditions:
    """Query conditions for deployment history."""

    # UUID filter conditions for history id
    @staticmethod
    def by_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentHistoryRow.id != spec.value
            return DeploymentHistoryRow.id == spec.value

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentHistoryRow.id.notin_(spec.values)
            return DeploymentHistoryRow.id.in_(spec.values)

        return inner

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
    def by_results(results: list[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.result.in_([str(r) for r in results])

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.error_code == error_code

        return inner

    # UUID filter conditions for deployment_id
    @staticmethod
    def by_deployment_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentHistoryRow.deployment_id != spec.value
            return DeploymentHistoryRow.deployment_id == spec.value

        return inner

    @staticmethod
    def by_deployment_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentHistoryRow.deployment_id.notin_(spec.values)
            return DeploymentHistoryRow.deployment_id.in_(spec.values)

        return inner

    # String filter conditions for error_code
    @staticmethod
    def by_error_code_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_error_code_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_error_code_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_error_code_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    # Status list filter conditions
    @staticmethod
    def by_from_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.from_status.in_(statuses)

        return inner

    @staticmethod
    def by_to_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.to_status.in_(statuses)

        return inner

    # String filter conditions for phase
    @staticmethod
    def by_phase_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], DeploymentHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_phase_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], DeploymentHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_phase_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], DeploymentHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_phase_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], DeploymentHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    # String filter conditions for message
    @staticmethod
    def by_message_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_message_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_message_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_message_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], DeploymentHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

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

    # DateTime filter conditions
    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.created_at == dt

        return inner

    @staticmethod
    def by_updated_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.updated_at < dt

        return inner

    @staticmethod
    def by_updated_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.updated_at > dt

        return inner

    @staticmethod
    def by_updated_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentHistoryRow.updated_at == dt

        return inner


class DeploymentHistoryOrders:
    """Query orders for deployment history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentHistoryRow.created_at.asc()
        return DeploymentHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentHistoryRow.updated_at.asc()
        return DeploymentHistoryRow.updated_at.desc()


# ========== Route History ==========


class RouteHistoryConditions:
    """Query conditions for route history."""

    # UUID filter conditions for history id
    @staticmethod
    def by_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return RouteHistoryRow.id != spec.value
            return RouteHistoryRow.id == spec.value

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return RouteHistoryRow.id.notin_(spec.values)
            return RouteHistoryRow.id.in_(spec.values)

        return inner

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
    def by_results(results: list[SchedulingResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.result.in_([str(r) for r in results])

        return inner

    @staticmethod
    def by_from_status(status: RouteStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return cast(sa.sql.expression.ColumnElement[bool], RouteHistoryRow.from_status == status.value)

        return inner

    @staticmethod
    def by_to_status(status: RouteStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return cast(sa.sql.expression.ColumnElement[bool], RouteHistoryRow.to_status == status.value)

        return inner

    @staticmethod
    def by_error_code(error_code: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.error_code == error_code

        return inner

    # UUID filter conditions for route_id
    @staticmethod
    def by_route_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return RouteHistoryRow.route_id != spec.value
            return RouteHistoryRow.route_id == spec.value

        return inner

    @staticmethod
    def by_route_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return RouteHistoryRow.route_id.notin_(spec.values)
            return RouteHistoryRow.route_id.in_(spec.values)

        return inner

    # UUID filter conditions for deployment_id
    @staticmethod
    def by_deployment_id_filter(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return RouteHistoryRow.deployment_id != spec.value
            return RouteHistoryRow.deployment_id == spec.value

        return inner

    @staticmethod
    def by_deployment_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return RouteHistoryRow.deployment_id.notin_(spec.values)
            return RouteHistoryRow.deployment_id.in_(spec.values)

        return inner

    # String filter conditions for error_code
    @staticmethod
    def by_error_code_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_error_code_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_error_code_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_error_code_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.error_code)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    # Status list filter conditions
    @staticmethod
    def by_from_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.from_status.in_(statuses)

        return inner

    @staticmethod
    def by_to_statuses(statuses: list[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.to_status.in_(statuses)

        return inner

    # String filter conditions for phase
    @staticmethod
    def by_phase_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], RouteHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_phase_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], RouteHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_phase_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], RouteHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_phase_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str], RouteHistoryRow.phase)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    # String filter conditions for message
    @staticmethod
    def by_message_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}%"
            else:
                pattern = f"%{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_message_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                val = spec.value.lower()
            else:
                val = spec.value
            if spec.negated:
                return col != val
            return col == val

        return inner

    @staticmethod
    def by_message_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"{spec.value.lower()}%"
            else:
                pattern = f"{spec.value}%"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

        return inner

    @staticmethod
    def by_message_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            col = cast(sa.ColumnElement[str | None], RouteHistoryRow.message)
            if spec.case_insensitive:
                col = sa.func.lower(col)
                pattern = f"%{spec.value.lower()}"
            else:
                pattern = f"%{spec.value}"
            expr = col.like(pattern)
            return ~expr if spec.negated else expr

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

    # DateTime filter conditions
    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.created_at == dt

        return inner

    @staticmethod
    def by_updated_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.updated_at < dt

        return inner

    @staticmethod
    def by_updated_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.updated_at > dt

        return inner

    @staticmethod
    def by_updated_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RouteHistoryRow.updated_at == dt

        return inner


class RouteHistoryOrders:
    """Query orders for route history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RouteHistoryRow.created_at.asc()
        return RouteHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RouteHistoryRow.updated_at.asc()
        return RouteHistoryRow.updated_at.desc()
