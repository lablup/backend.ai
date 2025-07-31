from typing import Optional, Sequence

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.scheduler.policies.policy import SchedulerPolicy


class FIFOPolicy(SchedulerPolicy):
    """First-In-First-Out scheduling policy."""

    def __init__(self, num_retries_to_skip: int = 0):
        self.num_retries_to_skip = num_retries_to_skip

    @property
    def name(self) -> str:
        return "fifo"

    async def apply(self) -> None:
        """Apply FIFO policy - no preprocessing needed."""
        pass

    def pick_session(
        self,
        pending_sessions: Sequence[SessionData],
    ) -> Optional[SessionId]:
        """
        Pick the first session from the pending sessions list.

        If num_retries_to_skip > 0, skip sessions that have failed
        more than the specified number of times to avoid HoL blocking.
        """
        if not pending_sessions:
            return None

        local_pending_sessions = list(pending_sessions)
        skipped_sessions: list[SessionData] = []

        while local_pending_sessions:
            session = local_pending_sessions.pop(0)

            if self.num_retries_to_skip == 0:  # Strict FIFO
                return SessionId(session.id)

            # Check retry count in status_data
            if session.status_data is not None:
                sched_data = session.status_data.get("scheduler", {})
                if sched_data.get("retries", 0) >= self.num_retries_to_skip:
                    skipped_sessions.append(session)
                    continue

            return SessionId(session.id)

        # If all sessions were skipped, pick the first skipped one
        if skipped_sessions:
            return SessionId(skipped_sessions[0].id)

        return None
