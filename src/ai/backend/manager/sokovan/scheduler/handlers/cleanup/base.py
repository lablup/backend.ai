"""Base handler class for cleanup operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.common.types import SessionId


class CleanupHandler(ABC):
    """Base class for cleanup handlers.

    Unlike SessionLifecycleHandler and KernelLifecycleHandler, cleanup handlers
    do not rely on the coordinator querying DB sessions by status. Instead, they
    read their work items from Valkey and perform cleanup operations directly.

    No status transitions are involved — the sessions are already in their final state.

    The coordinator calls the handler in two phases:
    1. ``fetch_session_ids()`` — read work items from Valkey (outside RecorderContext)
    2. ``execute(session_ids)`` — perform cleanup (inside RecorderContext set by coordinator)
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler for logging and metrics."""
        raise NotImplementedError("Subclasses must implement name()")

    @abstractmethod
    async def fetch_session_ids(self) -> Sequence[SessionId]:
        """Fetch session IDs that need cleanup from Valkey.

        Called by the coordinator before setting up RecorderContext.
        """
        raise NotImplementedError("Subclasses must implement fetch_session_ids()")

    @abstractmethod
    async def execute(self, session_ids: Sequence[SessionId]) -> None:
        """Execute the cleanup operation for the given session IDs.

        Called by the coordinator inside a RecorderContext scope.
        """
        raise NotImplementedError("Subclasses must implement execute()")
