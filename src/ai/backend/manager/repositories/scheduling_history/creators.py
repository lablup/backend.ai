"""CreatorSpec implementations for scheduling history entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    ReplicaGroupHandlerCategory,
    RouteHandlerCategory,
    RouteStatus,
    RouteSubStatus,
)
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
    SubStepResult,
)
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.repositories.base import CreatorSpec

__all__ = (
    "DeploymentHistoryCreatorSpec",
    "KernelSchedulingHistoryCreatorSpec",
    "ReplicaGroupHistoryCreatorSpec",
    "RouteHistoryCreatorSpec",
    "SessionSchedulingHistoryCreatorSpec",
)


@dataclass
class SessionSchedulingHistoryCreatorSpec(CreatorSpec[SessionSchedulingHistoryRow]):
    """CreatorSpec for session scheduling history."""

    session_id: SessionId
    phase: str  # ScheduleType value
    result: SchedulingResult
    message: str
    from_status: SessionStatus | None = None
    to_status: SessionStatus | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def build_row(self) -> SessionSchedulingHistoryRow:
        return SessionSchedulingHistoryRow(
            session_id=self.session_id,
            phase=self.phase,
            from_status=str(self.from_status) if self.from_status else None,
            to_status=str(self.to_status) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,  # PydanticListColumn handles serialization
            attempts=1,
        )


@dataclass
class KernelSchedulingHistoryCreatorSpec(CreatorSpec[KernelSchedulingHistoryRow]):
    """CreatorSpec for kernel scheduling history."""

    kernel_id: KernelId
    session_id: SessionId
    phase: str  # ScheduleType value
    result: SchedulingResult
    message: str
    from_status: KernelSchedulingPhase | None = None
    to_status: KernelSchedulingPhase | None = None
    error_code: str | None = None

    @override
    def build_row(self) -> KernelSchedulingHistoryRow:
        return KernelSchedulingHistoryRow(
            kernel_id=self.kernel_id,
            session_id=self.session_id,
            phase=self.phase,
            from_status=str(self.from_status) if self.from_status else None,
            to_status=str(self.to_status) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=1,
        )


@dataclass
class DeploymentHistoryCreatorSpec(CreatorSpec[DeploymentHistoryRow]):
    """CreatorSpec for deployment history."""

    deployment_id: DeploymentID
    phase: str  # DeploymentLifecycleType value
    result: SchedulingResult
    message: str
    handler_category: DeploymentHandlerCategory = DeploymentHandlerCategory.LIFECYCLE
    from_status: EndpointLifecycle | None = None
    to_status: EndpointLifecycle | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def build_row(self) -> DeploymentHistoryRow:
        return DeploymentHistoryRow(
            deployment_id=self.deployment_id,
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


@dataclass
class ReplicaGroupHistoryCreatorSpec(CreatorSpec[ReplicaGroupHistoryRow]):
    """CreatorSpec for replica-group history.

    ``from_status``/``to_status`` are plain strings because the meaning differs
    by category (scaling status vs lifecycle); the caller stringifies the right enum.
    """

    replica_group_id: ReplicaGroupID
    deployment_id: DeploymentID
    category: ReplicaGroupHandlerCategory
    phase: str
    result: SchedulingResult
    message: str
    from_status: str | None = None
    to_status: str | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def build_row(self) -> ReplicaGroupHistoryRow:
        return ReplicaGroupHistoryRow(
            replica_group_id=self.replica_group_id,
            deployment_id=self.deployment_id,
            category=self.category,
            phase=self.phase,
            from_status=self.from_status,
            to_status=self.to_status,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=1,
        )


@dataclass
class RouteHistoryCreatorSpec(CreatorSpec[RouteHistoryRow]):
    """CreatorSpec for route history."""

    route_id: ReplicaID
    deployment_id: DeploymentID
    category: RouteHandlerCategory
    phase: str  # RouteLifecycleType value
    result: SchedulingResult
    message: str
    from_status: RouteStatus | None = None
    to_status: RouteStatus | None = None
    from_sub_status: RouteSubStatus | None = None
    to_sub_status: RouteSubStatus | None = None
    error_code: str | None = None
    sub_steps: list[SubStepResult] = field(default_factory=list)

    @override
    def build_row(self) -> RouteHistoryRow:
        return RouteHistoryRow(
            route_id=self.route_id,
            deployment_id=self.deployment_id,
            category=self.category,
            phase=self.phase,
            from_status=self.from_status.value if self.from_status else None,
            to_status=self.to_status.value if self.to_status else None,
            from_sub_status=self.from_sub_status.value if self.from_sub_status else None,
            to_sub_status=self.to_sub_status.value if self.to_sub_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=self.sub_steps,
            attempts=1,
        )
