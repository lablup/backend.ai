"""Base keeper for health checks."""

from abc import ABC, abstractmethod
from typing import final

from ai.backend.common.types import SessionId

from ..results import HealthCheckResult
from ..types import SessionData


class HealthKeeper(ABC):
    """Base class for health keepers."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @abstractmethod
    def need_check(self, session: SessionData, current_time: float) -> bool:
        """Check if session needs health check based on time threshold.

        Args:
            session: Session data to check
            current_time: Current timestamp

        Returns:
            True if session needs health check, False otherwise
        """
        raise NotImplementedError("Subclasses must implement need_check()")

    @abstractmethod
    async def check_batch(
        self,
        sessions: list[SessionData],
    ) -> HealthCheckResult:
        """Perform health check for a batch of sessions.

        Args:
            sessions: List of session data to check

        Returns:
            Health check result with healthy and unhealthy session lists
        """
        raise NotImplementedError("Subclasses must implement check_batch()")

    @abstractmethod
    async def retry_unhealthy_sessions(
        self,
        unhealthy_sessions: list[SessionId],
    ) -> None:
        """Retry unhealthy sessions.

        Args:
            unhealthy_sessions: List of unhealthy session IDs
        """
        raise NotImplementedError("Subclasses must implement retry_unhealthy_sessions()")

    @final
    async def handle_batch(
        self,
        sessions: list[SessionData],
    ) -> HealthCheckResult:
        """Execute health checks in batch and handle failures."""
        import time

        current_time = time.time()

        # Filter sessions that need checking based on time threshold
        sessions_to_check = [
            session for session in sessions if self.need_check(session, current_time)
        ]

        if not sessions_to_check:
            # No sessions need checking
            return HealthCheckResult()

        result = await self.check_batch(sessions_to_check)

        # Retry unhealthy sessions if any
        if result.has_unhealthy_sessions():
            await self.retry_unhealthy_sessions(result.unhealthy_sessions)

        return result
