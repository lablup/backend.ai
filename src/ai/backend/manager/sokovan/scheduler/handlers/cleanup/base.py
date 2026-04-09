"""Base handler class for cleanup operations."""

from __future__ import annotations

from abc import ABC, abstractmethod


class CleanupHandler(ABC):
    """Base class for cleanup handlers.

    Unlike SessionLifecycleHandler and KernelLifecycleHandler, cleanup handlers
    do not rely on the coordinator querying DB sessions by status. Instead, they
    read their work items from Valkey and perform cleanup operations directly.

    No status transitions are involved — the sessions are already in their final state.
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler for logging and metrics."""
        raise NotImplementedError("Subclasses must implement name()")

    @abstractmethod
    async def execute(self) -> None:
        """Execute the cleanup operation.

        The handler is responsible for:
        1. Reading work items from Valkey
        2. Performing cleanup (e.g., sending RPC to agents)
        3. Removing processed items from Valkey
        """
        raise NotImplementedError("Subclasses must implement execute()")
