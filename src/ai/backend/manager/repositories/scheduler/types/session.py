"""Session related types."""

from dataclasses import dataclass
from functools import cached_property

from ai.backend.common.identifier.domain import DomainID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.sokovan import SessionWorkload


@dataclass
class PendingSessions:
    """Wrapper for pending session workloads with cached owner-key extraction."""

    sessions: list[SessionWorkload]

    @cached_property
    def user_uuids(self) -> set[UserID]:
        """Extract unique user IDs from pending sessions."""
        return {s.user_uuid for s in self.sessions}

    @cached_property
    def project_ids(self) -> set[ProjectID]:
        """Extract unique project IDs from pending sessions."""
        return {s.project_id for s in self.sessions}

    @cached_property
    def domain_ids(self) -> set[DomainID]:
        """Extract unique domain IDs from pending sessions."""
        return {s.domain_id for s in self.sessions}


@dataclass
class TerminatingKernelData:
    """Kernel data for termination processing."""

    kernel_id: KernelId
    status: KernelStatus
    container_id: str | None
    agent_id: AgentId | None
    agent_addr: str | None
    occupied_slots: ResourceSlot


@dataclass
class TerminatingSessionData:
    """Data for a session that needs to be terminated."""

    session_id: SessionId
    access_key: AccessKey
    creation_id: str
    status: SessionStatus
    status_info: str
    session_type: SessionTypes
    kernels: list[TerminatingKernelData]


@dataclass
class TerminatingKernelWithAgentData:
    """Kernel data with agent status for lost agent cleanup."""

    kernel_id: KernelId
    session_id: SessionId
    status: KernelStatus
    agent_id: AgentId | None
    agent_status: str | None  # Agent status from AgentRow


@dataclass
class KernelTerminationResult:
    """Result of termination for a single kernel."""

    kernel_id: KernelId
    agent_id: AgentId | None
    occupied_slots: ResourceSlot
    success: bool
    error: str | None = None


@dataclass
class SweptSessionInfo:
    """Information about a session that was swept during cleanup."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey


@dataclass
class MarkTerminatingResult:
    """Result of marking sessions for termination."""

    cancelled_sessions: list[SessionId]  # Sessions that were cancelled (PENDING)
    terminating_sessions: list[SessionId]  # Sessions marked as TERMINATING
    force_terminated_sessions: list[SessionId]  # Sessions directly set to TERMINATED (forced)
    skipped_sessions: list[
        SessionId
    ]  # Sessions not processed (already terminated, not found, etc.)

    def has_processed(self) -> bool:
        """Check if any sessions were actually processed (state changed)."""
        return bool(
            self.cancelled_sessions or self.terminating_sessions or self.force_terminated_sessions
        )

    def processed_count(self) -> int:
        """Get count of sessions that were actually processed."""
        return (
            len(self.cancelled_sessions)
            + len(self.terminating_sessions)
            + len(self.force_terminated_sessions)
        )
