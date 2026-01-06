"""
Result type for scheduling operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from ai.backend.common.types import AccessKey, AgentId, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.session import SessionStatus


@dataclass
class ScheduledSessionData:
    """Data for a scheduled session."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    reason: str


@dataclass
class ScheduleResult:
    """Result of a scheduling operation."""

    # List of scheduled session data
    scheduled_sessions: list[ScheduledSessionData] = field(default_factory=list)

    def needs_post_processing(self) -> bool:
        """Check if post-processing is needed based on the result."""
        return len(self.scheduled_sessions) > 0

    def success_count(self) -> int:
        """Get the count of successfully scheduled sessions."""
        return len(self.scheduled_sessions)


# ============================================================================
# New types for coordinator-handler pattern (DeploymentCoordinator style)
# ============================================================================


@dataclass
class SessionExecutionError:
    """Error information for a failed session operation."""

    session_id: SessionId
    reason: str
    error_detail: str


@dataclass
class HandlerKernelData:
    """Kernel data for handler execution.

    Contains minimal kernel information needed by handlers.
    """

    kernel_id: UUID
    agent_id: Optional[AgentId]
    status: KernelStatus
    container_id: Optional[str] = None
    occupied_slots: Optional[ResourceSlot] = None


@dataclass
class HandlerSessionData:
    """Session data passed to handlers by coordinator.

    Contains all necessary information for handler execution
    without requiring additional database queries for basic operations.
    """

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    status: SessionStatus
    scaling_group: str
    session_type: SessionTypes
    status_info: Optional[str] = None
    kernels: list[HandlerKernelData] = field(default_factory=list)


@dataclass
class SessionExecutionResult:
    """Result of a session lifecycle handler execution.

    Follows the DeploymentCoordinator pattern with successes, failures, and stales.
    Coordinator uses this result to apply status transitions.
    """

    successes: list[SessionId] = field(default_factory=list)
    failures: list[SessionExecutionError] = field(default_factory=list)
    stales: list[SessionId] = field(default_factory=list)
    # For post-processing (event broadcasting, cache invalidation)
    scheduled_data: list[ScheduledSessionData] = field(default_factory=list)

    def needs_post_processing(self) -> bool:
        """Check if post-processing is needed based on the result."""
        return len(self.scheduled_data) > 0

    def success_count(self) -> int:
        """Get the count of successfully processed sessions."""
        return len(self.successes)

    def merge(self, other: SessionExecutionResult) -> None:
        """Merge another result into this one."""
        self.successes.extend(other.successes)
        self.failures.extend(other.failures)
        self.stales.extend(other.stales)
        self.scheduled_data.extend(other.scheduled_data)
