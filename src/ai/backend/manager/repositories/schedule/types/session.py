"""Session related types."""

from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Optional
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.types import KernelWorkload, SessionWorkload


@dataclass
class KernelData:
    """Kernel data for scheduling."""

    id: UUID
    image: str
    architecture: str
    requested_slots: ResourceSlot
    agent: Optional[AgentId]

    def to_kernel_workload(self) -> KernelWorkload:
        """Convert to KernelWorkload entity."""
        return KernelWorkload(
            kernel_id=self.id,
            image=self.image,
            architecture=self.architecture,
            requested_slots=self.requested_slots,
        )


@dataclass
class PendingSessionData:
    """Pending session data for scheduling."""

    id: SessionId
    access_key: AccessKey
    requested_slots: ResourceSlot
    user_uuid: UUID
    group_id: UUID
    domain_name: str
    scaling_group_name: str
    priority: int
    session_type: SessionTypes
    cluster_mode: ClusterMode
    starts_at: Optional[datetime]
    is_private: bool
    designated_agent_ids: Optional[list[AgentId]]
    kernels: list[KernelData]

    def to_session_workload(self) -> SessionWorkload:
        """Convert to SessionWorkload entity."""
        kernel_workloads = [k.to_kernel_workload() for k in self.kernels]
        return SessionWorkload(
            session_id=self.id,
            access_key=self.access_key,
            requested_slots=self.requested_slots,
            user_uuid=self.user_uuid,
            group_id=self.group_id,
            domain_name=self.domain_name,
            scaling_group=self.scaling_group_name,
            priority=self.priority,
            session_type=self.session_type,
            cluster_mode=self.cluster_mode,
            starts_at=self.starts_at,
            is_private=self.is_private,
            kernels=kernel_workloads,
            designated_agent_ids=self.designated_agent_ids,
        )


@dataclass
class PendingSessions:
    """Wrapper for pending sessions with cached properties for entity extraction."""

    sessions: list[PendingSessionData]

    @cached_property
    def access_keys(self) -> set[AccessKey]:
        """Extract unique access keys from pending sessions."""
        return {s.access_key for s in self.sessions}

    @cached_property
    def user_uuids(self) -> set[UUID]:
        """Extract unique user UUIDs from pending sessions."""
        return {s.user_uuid for s in self.sessions}

    @cached_property
    def group_ids(self) -> set[UUID]:
        """Extract unique group IDs from pending sessions."""
        return {s.group_id for s in self.sessions}

    @cached_property
    def domain_names(self) -> set[str]:
        """Extract unique domain names from pending sessions."""
        return {s.domain_name for s in self.sessions}


@dataclass
class TerminatingKernelData:
    """Kernel data for termination processing."""

    kernel_id: str
    status: KernelStatus
    container_id: Optional[str]
    agent_id: Optional[AgentId]
    agent_addr: Optional[str]
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
class KernelTerminationResult:
    """Result of termination for a single kernel."""

    kernel_id: str
    agent_id: Optional[AgentId]
    occupied_slots: ResourceSlot
    success: bool
    error: Optional[str] = None


@dataclass
class SessionTerminationResult:
    """Result of termination for a session and its kernels."""

    session_id: SessionId
    access_key: AccessKey
    session_type: SessionTypes
    reason: str  # Termination reason (e.g., "USER_REQUESTED", "FORCE_TERMINATED")
    kernel_results: list[KernelTerminationResult] = field(default_factory=list)

    @property
    def should_terminate_session(self) -> bool:
        """Check if all kernels in the session were successfully terminated."""
        if not self.kernel_results:
            return False
        return all(kernel.success for kernel in self.kernel_results)


@dataclass
class SweptSessionInfo:
    """Information about a session that was swept during cleanup."""

    session_id: SessionId
    creation_id: str


@dataclass
class MarkTerminatingResult:
    """Result of marking sessions for termination."""

    cancelled_sessions: list[SessionId]  # Sessions that were cancelled (PENDING)
    terminating_sessions: list[SessionId]  # Sessions marked as TERMINATING
    skipped_sessions: list[
        SessionId
    ]  # Sessions not processed (already terminated, not found, etc.)

    def has_processed(self) -> bool:
        """Check if any sessions were actually processed (state changed)."""
        return bool(self.cancelled_sessions or self.terminating_sessions)

    def processed_count(self) -> int:
        """Get count of sessions that were actually processed."""
        return len(self.cancelled_sessions) + len(self.terminating_sessions)
