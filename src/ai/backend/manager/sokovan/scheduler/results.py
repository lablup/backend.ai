"""
Result type for scheduling operations.
"""

from dataclasses import dataclass, field

from ai.backend.common.types import AccessKey, SessionId


@dataclass
class ScheduledSessionData:
    """Data for a scheduled session."""

    session_id: SessionId
    creation_id: str
    access_key: AccessKey
    reason: str


@dataclass
class SessionOperationData:
    """Generic data for session operations."""

    session_id: SessionId
    reason: str = ""


@dataclass
class ScheduleResult:
    """Result of a scheduling operation."""

    # List of scheduled session data
    scheduled_sessions: list[ScheduledSessionData] = field(default_factory=list)

    # Sessions that passed precondition check (SCHEDULED -> PREPARING)
    prepared_sessions: list[SessionOperationData] = field(default_factory=list)

    # Sessions ready for starting (PREPARING/PULLING -> PREPARED)
    ready_sessions: list[SessionOperationData] = field(default_factory=list)

    # Sessions that started (PREPARED -> CREATING)
    started_sessions: list[SessionOperationData] = field(default_factory=list)

    # Sessions now running (CREATING -> RUNNING)
    running_sessions: list[SessionOperationData] = field(default_factory=list)

    # Sessions terminated (Any -> TERMINATING)
    terminated_sessions: list[SessionOperationData] = field(default_factory=list)

    # Sessions cleaned up (TERMINATING -> TERMINATED)
    cleaned_sessions: list[SessionOperationData] = field(default_factory=list)

    # Sessions swept (maintenance cleanup)
    swept_sessions: list[SessionOperationData] = field(default_factory=list)

    def needs_post_processing(self) -> bool:
        """Check if post-processing is needed based on the result."""
        return (
            len(self.scheduled_sessions) > 0
            or len(self.prepared_sessions) > 0
            or len(self.ready_sessions) > 0
            or len(self.started_sessions) > 0
            or len(self.running_sessions) > 0
            or len(self.terminated_sessions) > 0
            or len(self.cleaned_sessions) > 0
            or len(self.swept_sessions) > 0
        )

    def success_count(self) -> int:
        """Get the count of successfully processed sessions."""
        return (
            len(self.scheduled_sessions)
            + len(self.prepared_sessions)
            + len(self.ready_sessions)
            + len(self.started_sessions)
            + len(self.running_sessions)
            + len(self.terminated_sessions)
            + len(self.cleaned_sessions)
            + len(self.swept_sessions)
        )
