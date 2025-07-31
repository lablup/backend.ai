from abc import ABC, abstractmethod
from typing import Optional, Sequence

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionData


class SchedulerPolicy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the policy.
        This property should be implemented by subclasses to provide
        a unique identifier for the policy.
        """
        raise NotImplementedError("Subclasses must implement this property.")

    @abstractmethod
    async def apply(self) -> None:
        """
        Apply the scheduling policy.
        This method should be implemented by subclasses to define
        how the policy is applied to the scheduler.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def pick_session(
        self,
        pending_sessions: Sequence[SessionData],
        *args,
        **kwargs,
    ) -> Optional[SessionId]:
        """
        Pick a session from the pending sessions based on the policy.

        Args:
            pending_sessions: List of pending sessions to choose from
            *args, **kwargs: Additional arguments specific to each policy

        Returns:
            The ID of the selected session, or None if no session can be picked
        """
        raise NotImplementedError("Subclasses must implement this method.")
