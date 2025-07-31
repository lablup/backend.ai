from typing import Optional, Sequence

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.scheduler.policies.policy import SchedulerPolicy


class LIFOPolicy(SchedulerPolicy):
    """Last-In-First-Out scheduling policy."""

    @property
    def name(self) -> str:
        return "lifo"

    async def apply(self) -> None:
        """Apply LIFO policy - no preprocessing needed."""
        pass

    def pick_session(
        self,
        pending_sessions: Sequence[SessionData],
    ) -> Optional[SessionId]:
        """Pick the last session from the pending sessions list."""
        if not pending_sessions:
            return None

        return SessionId(pending_sessions[-1].id)
