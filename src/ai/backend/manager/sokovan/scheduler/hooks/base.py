"""Base classes for session state transition hooks."""

import logging
from abc import ABC, abstractmethod

from ai.backend.logging import BraceStyleAdapter

from ..types import SessionTransitionData

log = BraceStyleAdapter(logging.getLogger(__name__))


class SessionHook(ABC):
    """
    Abstract base class for session state transition hooks.
    Subclasses implement session-type specific logic.
    """

    @abstractmethod
    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        """
        Called when a session is about to transition from CREATING to RUNNING.
        Raises exception if the transition should not proceed.

        :param session: Session transition data with all necessary information
        :raises Exception: If the hook fails and transition should not proceed
        """
        raise NotImplementedError

    @abstractmethod
    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        """
        Called when a session is about to transition from TERMINATING to TERMINATED.
        Best-effort cleanup - exceptions are logged but don't prevent termination.

        :param session: Session transition data with all necessary information
        :raises Exception: If cleanup fails (will be logged but ignored)
        """
        raise NotImplementedError


class NoOpSessionHook(SessionHook):
    """Default no-op hook for session types that don't need special handling."""

    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        log.debug(
            "No-op hook for session {} (type: {})",
            session.session_id,
            session.session_type,
        )

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        log.debug(
            "No-op cleanup for session {} (type: {})",
            session.session_id,
            session.session_type,
        )
