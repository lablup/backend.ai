"""Health check result types."""

from dataclasses import dataclass, field

from ai.backend.common.types import SessionId


@dataclass
class HealthCheckResult:
    """Result of a batch health check operation."""

    healthy_sessions: list[SessionId] = field(default_factory=list)
    unhealthy_sessions: list[SessionId] = field(default_factory=list)

    def has_unhealthy_sessions(self) -> bool:
        """Check if there are any unhealthy sessions."""
        return len(self.unhealthy_sessions) > 0
