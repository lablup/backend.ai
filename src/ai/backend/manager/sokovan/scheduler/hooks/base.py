"""Base classes for session state transition hooks."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ai.backend.logging import BraceStyleAdapter

from ..types import SessionTransitionData

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class HookResult:
    """Result of a hook execution."""

    success: bool
    message: str = ""
    error: Optional[Exception] = None

    @classmethod
    def ok(cls, message: str = "Hook executed successfully") -> "HookResult":
        """Create a successful result."""
        return cls(success=True, message=message)

    @classmethod
    def fail(cls, message: str, error: Optional[Exception] = None) -> "HookResult":
        """Create a failed result."""
        return cls(success=False, message=message, error=error)


class SessionHook(ABC):
    """
    Abstract base class for session state transition hooks.
    Subclasses implement session-type specific logic.
    """

    @abstractmethod
    async def on_transition_to_running(self, session: SessionTransitionData) -> HookResult:
        """
        Called when a session is about to transition from CREATING to RUNNING.
        Must succeed for the transition to proceed.

        :param session: Session transition data with all necessary information
        :return: HookResult indicating success or failure
        """
        raise NotImplementedError

    @abstractmethod
    async def on_transition_to_terminated(self, session: SessionTransitionData) -> HookResult:
        """
        Called when a session is about to transition from TERMINATING to TERMINATED.
        Best-effort cleanup - failures are logged but don't prevent termination.

        :param session: Session transition data with all necessary information
        :return: HookResult indicating success or failure
        """
        raise NotImplementedError


class NoOpSessionHook(SessionHook):
    """Default no-op hook for session types that don't need special handling."""

    async def on_transition_to_running(self, session: SessionTransitionData) -> HookResult:
        """No special action needed."""
        log.debug(
            "No-op hook for session {} (type: {})",
            session.session_id,
            session.session_type,
        )
        return HookResult.ok()

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> HookResult:
        """No special cleanup needed."""
        log.debug(
            "No-op cleanup for session {} (type: {})",
            session.session_id,
            session.session_type,
        )
        return HookResult.ok()
