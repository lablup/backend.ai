"""Creator specs for the session, kernel, deployment and route history tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_history import DeploymentHistoryID
from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.kernel_scheduling_history import KernelSchedulingHistoryID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.route_history import RouteHistoryID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.session_scheduling_history import SessionSchedulingHistoryID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentHistoryData,
    RouteHandlerCategory,
    RouteHistoryData,
    RouteStatus,
    RouteSubStatus,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryData,
    KernelSchedulingPhase,
)
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionSchedulingHistoryData,
    SessionStatus,
    SubStepResult,
)
from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class DeploymentHistoryCreator(
    FieldCreator[DeploymentID, DeploymentHistoryRow, DeploymentHistoryData]
):
    """Records one lifecycle or scaling transition of the deployment it belongs to."""

    phase: str
    result: SchedulingResult
    message: str
    handler_category: DeploymentHandlerCategory = DeploymentHandlerCategory.LIFECYCLE
    from_status: EndpointLifecycle | None = None
    to_status: EndpointLifecycle | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def field_id(self, row: DeploymentHistoryRow) -> DeploymentHistoryID:
        return DeploymentHistoryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> DeploymentHistoryRow:
        return DeploymentHistoryRow(
            deployment_id=owner_id,
            handler_category=self.handler_category,
            phase=self.phase,
            from_status=str(self.from_status.value) if self.from_status else None,
            to_status=str(self.to_status.value) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=1,
        )

    @override
    def to_data(self, row: DeploymentHistoryRow) -> DeploymentHistoryData:
        return row.to_data()


@dataclass
class RouteHistoryCreator(FieldCreator[DeploymentID, RouteHistoryRow, RouteHistoryData]):
    """Records one transition of a replica, under the deployment it serves."""

    route_id: ReplicaID
    category: RouteHandlerCategory
    phase: str
    result: SchedulingResult
    message: str
    from_status: RouteStatus | None = None
    to_status: RouteStatus | None = None
    from_sub_status: RouteSubStatus | None = None
    to_sub_status: RouteSubStatus | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def field_id(self, row: RouteHistoryRow) -> RouteHistoryID:
        return RouteHistoryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> RouteHistoryRow:
        return RouteHistoryRow(
            route_id=self.route_id,
            deployment_id=owner_id,
            category=self.category,
            phase=self.phase,
            from_status=str(self.from_status.value) if self.from_status else None,
            to_status=str(self.to_status.value) if self.to_status else None,
            from_sub_status=str(self.from_sub_status.value) if self.from_sub_status else None,
            to_sub_status=str(self.to_sub_status.value) if self.to_sub_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=1,
        )

    @override
    def to_data(self, row: RouteHistoryRow) -> RouteHistoryData:
        return row.to_data()


@dataclass
class SessionSchedulingHistoryCreator(
    FieldCreator[SessionID, SessionSchedulingHistoryRow, SessionSchedulingHistoryData]
):
    """Records one scheduling transition of the session it belongs to."""

    phase: str
    result: SchedulingResult
    message: str
    from_status: SessionStatus | None = None
    to_status: SessionStatus | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def field_id(self, row: SessionSchedulingHistoryRow) -> SessionSchedulingHistoryID:
        return SessionSchedulingHistoryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: SessionID) -> SessionSchedulingHistoryRow:
        return SessionSchedulingHistoryRow(
            session_id=owner_id,
            phase=self.phase,
            from_status=str(self.from_status) if self.from_status else None,
            to_status=str(self.to_status) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=1,
        )

    @override
    def to_data(self, row: SessionSchedulingHistoryRow) -> SessionSchedulingHistoryData:
        return row.to_data()


@dataclass
class KernelSchedulingHistoryCreator(
    FieldCreator[SessionID, KernelSchedulingHistoryRow, KernelSchedulingHistoryData]
):
    """Records one transition of a kernel, under the session it runs in."""

    kernel_id: KernelID
    phase: str
    result: SchedulingResult
    message: str
    from_status: KernelSchedulingPhase | None = None
    to_status: KernelSchedulingPhase | None = None
    error_code: str | None = None

    @override
    def field_id(self, row: KernelSchedulingHistoryRow) -> KernelSchedulingHistoryID:
        return KernelSchedulingHistoryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: SessionID) -> KernelSchedulingHistoryRow:
        return KernelSchedulingHistoryRow(
            kernel_id=self.kernel_id,
            session_id=owner_id,
            phase=self.phase,
            from_status=str(self.from_status) if self.from_status else None,
            to_status=str(self.to_status) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=1,
        )

    @override
    def to_data(self, row: KernelSchedulingHistoryRow) -> KernelSchedulingHistoryData:
        return row.to_data()
