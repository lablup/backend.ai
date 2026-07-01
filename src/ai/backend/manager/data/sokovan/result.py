"""Result types for scheduler execution operations."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.data.session.types import KernelMatchType
from ai.backend.manager.exceptions import ErrorStatusInfo
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.session import SessionStatus

from .lifecycle import SessionWithKernels


@dataclass
class SessionStartResult:
    """Result of a session start operation."""

    session_id: SessionId
    success: bool
    error: str | None = None
    error_info: ErrorStatusInfo | None = None


@dataclass
class SchedulerExecutionError:
    """
    Represents a failed scheduler operation.

    Steps/history are managed separately via RecorderContext at coordinator level.
    """

    session_with_kernels: SessionWithKernels
    reason: str
    error_detail: str


@dataclass
class SchedulerExecutionResult:
    """
    Result of a scheduler handler execution.

    Follows the deployment pattern with successes, errors, and skipped lists.
    Steps/history are managed separately via RecorderContext at coordinator level.
    """

    successes: list[SessionWithKernels] = field(default_factory=list)
    errors: list[SchedulerExecutionError] = field(default_factory=list)
    skipped: list[SessionWithKernels] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        """Check if there are any failed operations."""
        return len(self.errors) > 0


@dataclass
class KernelTerminationInfo:
    """Information about a kernel to be terminated.

    Used by SessionExecutionResult to communicate kernel terminations
    that should be processed by the Coordinator together with session status changes.
    """

    kernel_id: KernelId
    reason: str


@dataclass
class SweepStaleKernelsResult:
    """Result of sweep_stale_kernels_for_handler operation.

    Contains both the dead kernel IDs and affected sessions for the Coordinator
    to process kernel terminations and session updates.
    """

    dead_kernel_ids: list[KernelId]
    affected_sessions: list[SessionWithKernels]


@dataclass
class RetryResult:
    """Result of retry_*_for_handler operations in Launcher.

    Used to communicate retried sessions and exceeded sessions to handlers
    for Coordinator to process status changes.
    """

    retried_ids: list[SessionId]
    exceeded_ids: list[SessionId]


@dataclass(frozen=True)
class PromotionSpec:
    """Specification for session promotion operations.

    Replaces promotion handlers with a declarative spec. The Coordinator
    processes promotions directly based on these specs.
    """

    name: str
    target_statuses: list[SessionStatus]
    target_kernel_statuses: list[KernelStatus]
    kernel_match_type: KernelMatchType
    success_status: SessionStatus
    reason: str
