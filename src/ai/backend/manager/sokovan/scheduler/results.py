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
from ai.backend.manager.sokovan.scheduler.types import KernelTerminationInfo, SessionRunningData


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
class SessionTransitionInfo:
    """Session transition information for history recording and event broadcasting.

    Contains session_id with its actual from_status at the time of processing.
    Also includes creation_id and access_key for:
    - Event broadcasting (session_id, creation_id, reason)
    - Cache invalidation (access_key)
    """

    session_id: SessionId
    from_status: SessionStatus
    reason: Optional[str] = None
    creation_id: Optional[str] = None
    access_key: Optional[AccessKey] = None


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
    """Result of a session lifecycle handler execution (BEP-1030).

    Follows the DeploymentCoordinator pattern with successes, failures, and skipped.
    Handler reports what happened, Coordinator applies policy (retry count, timeout)
    to determine the outcome (need_retry/expired/give_up) for failures.

    Fields:
    - successes: Sessions that completed successfully
    - failures: Sessions that failed (Coordinator determines retry/expired/give_up)
    - skipped: Sessions that were skipped (no action needed, no status change)
    """

    # Handler outcome fields
    successes: list[SessionTransitionInfo] = field(default_factory=list)
    failures: list[SessionTransitionInfo] = field(default_factory=list)
    skipped: list[SessionTransitionInfo] = field(default_factory=list)

    # Kernel terminations to be processed together with session status changes
    # Note: Will be moved to KernelExecutionResult in Phase 3
    kernel_terminations: list[KernelTerminationInfo] = field(default_factory=list)
    # Sessions transitioning to RUNNING with their occupied_slots
    # Note: Will be removed in Phase 2 with batch hook processing
    sessions_running_data: list[SessionRunningData] = field(default_factory=list)

    def success_count(self) -> int:
        """Get the count of successfully processed sessions."""
        return len(self.successes)

    def success_ids(self) -> list[SessionId]:
        """Get list of successful session IDs."""
        return [s.session_id for s in self.successes]

    def failure_ids(self) -> list[SessionId]:
        """Get list of failed session IDs."""
        return [s.session_id for s in self.failures]

    def skipped_ids(self) -> list[SessionId]:
        """Get list of skipped session IDs."""
        return [s.session_id for s in self.skipped]

    def merge(self, other: SessionExecutionResult) -> None:
        """Merge another result into this one."""
        self.successes.extend(other.successes)
        self.failures.extend(other.failures)
        self.skipped.extend(other.skipped)
        self.kernel_terminations.extend(other.kernel_terminations)
        self.sessions_running_data.extend(other.sessions_running_data)
