"""
Common entities returned by ScheduleRepository.
These are the final, transformed data structures that the repository returns.
"""

from dataclasses import dataclass, field
from typing import Optional

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentInfo
from ai.backend.manager.sokovan.scheduler.types import (
    SessionWorkload,
    SystemSnapshot,
)


@dataclass
class SchedulingConfig:
    """Combined scheduling configuration including scaling group info and scheduler settings."""

    # From ScalingGroupInfo
    scheduler_name: str
    agent_selection_strategy: str

    # From original SchedulingConfig
    max_container_count_per_agent: Optional[int]
    enforce_spreading_endpoint_replica: bool


@dataclass
class SchedulingContextData:
    """Processed data ready for scheduling decisions."""

    scheduling_config: SchedulingConfig
    pending_sessions: list[SessionWorkload]
    system_snapshot: SystemSnapshot
    agents: list[AgentInfo]


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

    cancelled_sessions: list[str]  # Sessions that were cancelled (PENDING/PULLING)
    terminating_sessions: list[str]  # Sessions marked as TERMINATING
    skipped_sessions: list[str]  # Sessions already TERMINATED/CANCELLED/TERMINATING
    not_found_sessions: list[str]  # Sessions that don't exist

    def has_processed(self) -> bool:
        """Check if any sessions were actually processed (state changed)."""
        return bool(self.cancelled_sessions or self.terminating_sessions)

    def processed_count(self) -> int:
        """Get count of sessions that were actually processed."""
        return len(self.cancelled_sessions) + len(self.terminating_sessions)
