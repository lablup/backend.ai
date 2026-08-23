"""CreatorSpec implementations for scheduling history entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
    SubStepResult,
)
from ai.backend.manager.models.scheduling_history import (
    KernelSchedulingHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.repositories.base import CreatorSpec

__all__ = (
    "KernelSchedulingHistoryCreatorSpec",
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
