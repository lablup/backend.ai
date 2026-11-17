"""What a scheduling history search can filter and order by, and how a row becomes data.

``sub_steps`` is JSONB, so both slots stay empty; ``message`` is ``sa.Text`` with no index
serving a partial match, so it carries equality and membership only.
"""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentHistoryData,
    RouteHandlerCategory,
    RouteHistoryData,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryData,
    KernelSchedulingPhase,
)
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SessionStatus,
)
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import QueryColumn


class _SessionSchedulingHistoryOwnColumns(
    RowDataConverter[SessionSchedulingHistoryRow, SessionSchedulingHistoryData]
):
    """The session history row's own columns."""

    id = QueryColumn(
        SessionSchedulingHistoryRow.id,
        UUIDConditions(SessionSchedulingHistoryRow.id),
        ColumnOrder(SessionSchedulingHistoryRow.id),
    )
    session_id = QueryColumn(
        SessionSchedulingHistoryRow.session_id,
        UUIDConditions(SessionSchedulingHistoryRow.session_id),
        ColumnOrder(SessionSchedulingHistoryRow.session_id),
    )
    phase = QueryColumn(
        SessionSchedulingHistoryRow.phase,
        StringConditions(SessionSchedulingHistoryRow.phase),
        ColumnOrder(SessionSchedulingHistoryRow.phase),
    )
    from_status = QueryColumn(
        SessionSchedulingHistoryRow.from_status,
        StringConditions(SessionSchedulingHistoryRow.from_status),
        ColumnOrder(SessionSchedulingHistoryRow.from_status),
    )
    to_status = QueryColumn(
        SessionSchedulingHistoryRow.to_status,
        StringConditions(SessionSchedulingHistoryRow.to_status),
        ColumnOrder(SessionSchedulingHistoryRow.to_status),
    )
    result = QueryColumn(
        SessionSchedulingHistoryRow.result,
        EnumConditions(SessionSchedulingHistoryRow.result, SchedulingResult),
        ColumnOrder(SessionSchedulingHistoryRow.result),
    )
    error_code = QueryColumn(
        SessionSchedulingHistoryRow.error_code,
        StringConditions(SessionSchedulingHistoryRow.error_code),
        ColumnOrder(SessionSchedulingHistoryRow.error_code),
    )
    message = QueryColumn(
        SessionSchedulingHistoryRow.message,
        StringEqualityConditions(SessionSchedulingHistoryRow.message),
        None,
    )
    sub_steps = QueryColumn(SessionSchedulingHistoryRow.sub_steps, None, None)
    attempts = QueryColumn(
        SessionSchedulingHistoryRow.attempts,
        IntConditions(SessionSchedulingHistoryRow.attempts),
        ColumnOrder(SessionSchedulingHistoryRow.attempts),
    )
    created_at = QueryColumn(
        SessionSchedulingHistoryRow.created_at,
        DateTimeConditions(SessionSchedulingHistoryRow.created_at),
        ColumnOrder(SessionSchedulingHistoryRow.created_at),
    )
    updated_at = QueryColumn(
        SessionSchedulingHistoryRow.updated_at,
        DateTimeConditions(SessionSchedulingHistoryRow.updated_at),
        ColumnOrder(SessionSchedulingHistoryRow.updated_at),
    )

    @override
    def to_data(self, row: SessionSchedulingHistoryRow) -> SessionSchedulingHistoryData:
        from_status = self.from_status.read(row)
        to_status = self.to_status.read(row)
        return SessionSchedulingHistoryData(
            id=self.id.read(row),
            session_id=SessionId(self.session_id.read(row)),
            phase=self.phase.read(row),
            from_status=SessionStatus(from_status) if from_status else None,
            to_status=SessionStatus(to_status) if to_status else None,
            result=SchedulingResult(self.result.read(row)),
            error_code=self.error_code.read(row),
            message=self.message.read(row),
            sub_steps=self.sub_steps.read(row),
            attempts=self.attempts.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _KernelSchedulingHistoryOwnColumns(
    RowDataConverter[KernelSchedulingHistoryRow, KernelSchedulingHistoryData]
):
    """The kernel history row's own columns."""

    id = QueryColumn(
        KernelSchedulingHistoryRow.id,
        UUIDConditions(KernelSchedulingHistoryRow.id),
        ColumnOrder(KernelSchedulingHistoryRow.id),
    )
    kernel_id = QueryColumn(
        KernelSchedulingHistoryRow.kernel_id,
        UUIDConditions(KernelSchedulingHistoryRow.kernel_id),
        ColumnOrder(KernelSchedulingHistoryRow.kernel_id),
    )
    session_id = QueryColumn(
        KernelSchedulingHistoryRow.session_id,
        UUIDConditions(KernelSchedulingHistoryRow.session_id),
        ColumnOrder(KernelSchedulingHistoryRow.session_id),
    )
    phase = QueryColumn(
        KernelSchedulingHistoryRow.phase,
        StringConditions(KernelSchedulingHistoryRow.phase),
        ColumnOrder(KernelSchedulingHistoryRow.phase),
    )
    from_status = QueryColumn(
        KernelSchedulingHistoryRow.from_status,
        StringConditions(KernelSchedulingHistoryRow.from_status),
        ColumnOrder(KernelSchedulingHistoryRow.from_status),
    )
    to_status = QueryColumn(
        KernelSchedulingHistoryRow.to_status,
        StringConditions(KernelSchedulingHistoryRow.to_status),
        ColumnOrder(KernelSchedulingHistoryRow.to_status),
    )
    result = QueryColumn(
        KernelSchedulingHistoryRow.result,
        EnumConditions(KernelSchedulingHistoryRow.result, SchedulingResult),
        ColumnOrder(KernelSchedulingHistoryRow.result),
    )
    error_code = QueryColumn(
        KernelSchedulingHistoryRow.error_code,
        StringConditions(KernelSchedulingHistoryRow.error_code),
        ColumnOrder(KernelSchedulingHistoryRow.error_code),
    )
    message = QueryColumn(
        KernelSchedulingHistoryRow.message,
        StringEqualityConditions(KernelSchedulingHistoryRow.message),
        None,
    )
    attempts = QueryColumn(
        KernelSchedulingHistoryRow.attempts,
        IntConditions(KernelSchedulingHistoryRow.attempts),
        ColumnOrder(KernelSchedulingHistoryRow.attempts),
    )
    created_at = QueryColumn(
        KernelSchedulingHistoryRow.created_at,
        DateTimeConditions(KernelSchedulingHistoryRow.created_at),
        ColumnOrder(KernelSchedulingHistoryRow.created_at),
    )
    updated_at = QueryColumn(
        KernelSchedulingHistoryRow.updated_at,
        DateTimeConditions(KernelSchedulingHistoryRow.updated_at),
        ColumnOrder(KernelSchedulingHistoryRow.updated_at),
    )

    @override
    def to_data(self, row: KernelSchedulingHistoryRow) -> KernelSchedulingHistoryData:
        from_status = self.from_status.read(row)
        to_status = self.to_status.read(row)
        return KernelSchedulingHistoryData(
            id=KernelSchedulingHistoryID(self.id.read(row)),
            kernel_id=KernelId(self.kernel_id.read(row)),
            session_id=SessionId(self.session_id.read(row)),
            phase=self.phase.read(row),
            from_status=KernelSchedulingPhase(from_status) if from_status else None,
            to_status=KernelSchedulingPhase(to_status) if to_status else None,
            result=SchedulingResult(self.result.read(row)),
            error_code=self.error_code.read(row),
            message=self.message.read(row),
            attempts=self.attempts.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _DeploymentHistoryOwnColumns(RowDataConverter[DeploymentHistoryRow, DeploymentHistoryData]):
    """The deployment history row's own columns."""

    id = QueryColumn(
        DeploymentHistoryRow.id,
        UUIDConditions(DeploymentHistoryRow.id),
        ColumnOrder(DeploymentHistoryRow.id),
    )
    deployment_id = QueryColumn(
        DeploymentHistoryRow.deployment_id,
        UUIDConditions(DeploymentHistoryRow.deployment_id),
        ColumnOrder(DeploymentHistoryRow.deployment_id),
    )
    handler_category = QueryColumn(
        DeploymentHistoryRow.handler_category,
        EnumConditions(DeploymentHistoryRow.handler_category, DeploymentHandlerCategory),
        ColumnOrder(DeploymentHistoryRow.handler_category),
    )
    phase = QueryColumn(
        DeploymentHistoryRow.phase,
        StringConditions(DeploymentHistoryRow.phase),
        ColumnOrder(DeploymentHistoryRow.phase),
    )
    from_status = QueryColumn(
        DeploymentHistoryRow.from_status,
        StringConditions(DeploymentHistoryRow.from_status),
        ColumnOrder(DeploymentHistoryRow.from_status),
    )
    to_status = QueryColumn(
        DeploymentHistoryRow.to_status,
        StringConditions(DeploymentHistoryRow.to_status),
        ColumnOrder(DeploymentHistoryRow.to_status),
    )
    result = QueryColumn(
        DeploymentHistoryRow.result,
        EnumConditions(DeploymentHistoryRow.result, SchedulingResult),
        ColumnOrder(DeploymentHistoryRow.result),
    )
    error_code = QueryColumn(
        DeploymentHistoryRow.error_code,
        StringConditions(DeploymentHistoryRow.error_code),
        ColumnOrder(DeploymentHistoryRow.error_code),
    )
    message = QueryColumn(
        DeploymentHistoryRow.message,
        StringEqualityConditions(DeploymentHistoryRow.message),
        None,
    )
    sub_steps = QueryColumn(DeploymentHistoryRow.sub_steps, None, None)
    attempts = QueryColumn(
        DeploymentHistoryRow.attempts,
        IntConditions(DeploymentHistoryRow.attempts),
        ColumnOrder(DeploymentHistoryRow.attempts),
    )
    created_at = QueryColumn(
        DeploymentHistoryRow.created_at,
        DateTimeConditions(DeploymentHistoryRow.created_at),
        ColumnOrder(DeploymentHistoryRow.created_at),
    )
    updated_at = QueryColumn(
        DeploymentHistoryRow.updated_at,
        DateTimeConditions(DeploymentHistoryRow.updated_at),
        ColumnOrder(DeploymentHistoryRow.updated_at),
    )

    @override
    def to_data(self, row: DeploymentHistoryRow) -> DeploymentHistoryData:
        from_status = self.from_status.read(row)
        to_status = self.to_status.read(row)
        return DeploymentHistoryData(
            id=self.id.read(row),
            deployment_id=self.deployment_id.read(row),
            handler_category=self.handler_category.read(row),
            phase=self.phase.read(row),
            from_status=ModelDeploymentStatus(from_status) if from_status else None,
            to_status=ModelDeploymentStatus(to_status) if to_status else None,
            result=SchedulingResult(self.result.read(row)),
            error_code=self.error_code.read(row),
            message=self.message.read(row),
            sub_steps=self.sub_steps.read(row),
            attempts=self.attempts.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class _RouteHistoryOwnColumns(RowDataConverter[RouteHistoryRow, RouteHistoryData]):
    """The route history row's own columns."""

    id = QueryColumn(
        RouteHistoryRow.id, UUIDConditions(RouteHistoryRow.id), ColumnOrder(RouteHistoryRow.id)
    )
    route_id = QueryColumn(
        RouteHistoryRow.route_id,
        UUIDConditions(RouteHistoryRow.route_id),
        ColumnOrder(RouteHistoryRow.route_id),
    )
    deployment_id = QueryColumn(
        RouteHistoryRow.deployment_id,
        UUIDConditions(RouteHistoryRow.deployment_id),
        ColumnOrder(RouteHistoryRow.deployment_id),
    )
    category = QueryColumn(
        RouteHistoryRow.category,
        EnumConditions(RouteHistoryRow.category, RouteHandlerCategory),
        ColumnOrder(RouteHistoryRow.category),
    )
    phase = QueryColumn(
        RouteHistoryRow.phase,
        StringConditions(RouteHistoryRow.phase),
        ColumnOrder(RouteHistoryRow.phase),
    )
    from_status = QueryColumn(
        RouteHistoryRow.from_status,
        StringConditions(RouteHistoryRow.from_status),
        ColumnOrder(RouteHistoryRow.from_status),
    )
    to_status = QueryColumn(
        RouteHistoryRow.to_status,
        StringConditions(RouteHistoryRow.to_status),
        ColumnOrder(RouteHistoryRow.to_status),
    )
    from_sub_status = QueryColumn(
        RouteHistoryRow.from_sub_status,
        StringConditions(RouteHistoryRow.from_sub_status),
        ColumnOrder(RouteHistoryRow.from_sub_status),
    )
    to_sub_status = QueryColumn(
        RouteHistoryRow.to_sub_status,
        StringConditions(RouteHistoryRow.to_sub_status),
        ColumnOrder(RouteHistoryRow.to_sub_status),
    )
    result = QueryColumn(
        RouteHistoryRow.result,
        EnumConditions(RouteHistoryRow.result, SchedulingResult),
        ColumnOrder(RouteHistoryRow.result),
    )
    error_code = QueryColumn(
        RouteHistoryRow.error_code,
        StringConditions(RouteHistoryRow.error_code),
        ColumnOrder(RouteHistoryRow.error_code),
    )
    message = QueryColumn(
        RouteHistoryRow.message, StringEqualityConditions(RouteHistoryRow.message), None
    )
    sub_steps = QueryColumn(RouteHistoryRow.sub_steps, None, None)
    attempts = QueryColumn(
        RouteHistoryRow.attempts,
        IntConditions(RouteHistoryRow.attempts),
        ColumnOrder(RouteHistoryRow.attempts),
    )
    created_at = QueryColumn(
        RouteHistoryRow.created_at,
        DateTimeConditions(RouteHistoryRow.created_at),
        ColumnOrder(RouteHistoryRow.created_at),
    )
    updated_at = QueryColumn(
        RouteHistoryRow.updated_at,
        DateTimeConditions(RouteHistoryRow.updated_at),
        ColumnOrder(RouteHistoryRow.updated_at),
    )

    @override
    def to_data(self, row: RouteHistoryRow) -> RouteHistoryData:
        return RouteHistoryData(
            id=self.id.read(row),
            route_id=self.route_id.read(row),
            deployment_id=self.deployment_id.read(row),
            category=self.category.read(row),
            phase=self.phase.read(row),
            from_status=self.from_status.read(row),
            to_status=self.to_status.read(row),
            from_sub_status=self.from_sub_status.read(row),
            to_sub_status=self.to_sub_status.read(row),
            result=SchedulingResult(self.result.read(row)),
            error_code=self.error_code.read(row),
            message=self.message.read(row),
            sub_steps=self.sub_steps.read(row),
            attempts=self.attempts.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class SessionSchedulingHistoryQuerySpec:
    own = _SessionSchedulingHistoryOwnColumns()


class KernelSchedulingHistoryQuerySpec:
    own = _KernelSchedulingHistoryOwnColumns()


class DeploymentHistoryQuerySpec:
    own = _DeploymentHistoryOwnColumns()


class RouteHistoryQuerySpec:
    own = _RouteHistoryOwnColumns()
