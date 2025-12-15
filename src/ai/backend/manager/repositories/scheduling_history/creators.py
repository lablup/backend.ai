"""CreatorSpec implementations for scheduling history entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.common.data.model_deployment.types import ModelDeploymentStatus
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
    SubStepResult,
)
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.repositories.base import CreatorSpec

__all__ = (
    "SessionSchedulingHistoryCreatorSpec",
    "KernelSchedulingHistoryCreatorSpec",
    "DeploymentHistoryCreatorSpec",
    "RouteHistoryCreatorSpec",
)


@dataclass
class SessionSchedulingHistoryCreatorSpec(CreatorSpec[SessionSchedulingHistoryRow]):
    """CreatorSpec for session scheduling history."""

    session_id: SessionId
    phase: str  # ScheduleType value
    result: SchedulingResult
    message: str
    from_status: Optional[SessionStatus] = None
    to_status: Optional[SessionStatus] = None
    error_code: Optional[str] = None
    sub_steps: Optional[list[SubStepResult]] = None

    @override
    def build_row(self) -> SessionSchedulingHistoryRow:
        sub_steps_json: list[dict[str, Any]] | None = None
        if self.sub_steps:
            sub_steps_json = [s.model_dump(mode="json") for s in self.sub_steps]
        return SessionSchedulingHistoryRow(
            session_id=self.session_id,
            phase=self.phase,
            from_status=str(self.from_status) if self.from_status else None,
            to_status=str(self.to_status) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            sub_steps=sub_steps_json,
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
    from_status: Optional[KernelSchedulingPhase] = None
    to_status: Optional[KernelSchedulingPhase] = None
    error_code: Optional[str] = None

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

    deployment_id: UUID
    phase: str  # DeploymentLifecycleType value
    result: SchedulingResult
    message: str
    from_status: Optional[ModelDeploymentStatus] = None
    to_status: Optional[ModelDeploymentStatus] = None
    error_code: Optional[str] = None

    @override
    def build_row(self) -> DeploymentHistoryRow:
        return DeploymentHistoryRow(
            deployment_id=self.deployment_id,
            phase=self.phase,
            from_status=str(self.from_status) if self.from_status else None,
            to_status=str(self.to_status) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=1,
        )


@dataclass
class RouteHistoryCreatorSpec(CreatorSpec[RouteHistoryRow]):
    """CreatorSpec for route history."""

    route_id: UUID
    deployment_id: UUID
    phase: str  # RouteLifecycleType value
    result: SchedulingResult
    message: str
    from_status: Optional[RouteStatus] = None
    to_status: Optional[RouteStatus] = None
    error_code: Optional[str] = None

    @override
    def build_row(self) -> RouteHistoryRow:
        return RouteHistoryRow(
            route_id=self.route_id,
            deployment_id=self.deployment_id,
            phase=self.phase,
            from_status=str(self.from_status.value) if self.from_status else None,
            to_status=str(self.to_status.value) if self.to_status else None,
            result=str(self.result),
            error_code=self.error_code,
            message=self.message,
            attempts=1,
        )
