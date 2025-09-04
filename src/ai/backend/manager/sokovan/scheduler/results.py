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
