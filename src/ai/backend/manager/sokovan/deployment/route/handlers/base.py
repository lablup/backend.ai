"""Base class for route lifecycle handlers."""

from abc import abstractmethod
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.model_serving.types import RouteStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


class RouteHandler:
    """Base class for route operation handlers."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @property
    @abstractmethod
    def lock_id(self) -> Optional[LockID]:
        """Get the lock ID for this handler.

        Returns:
            LockID to acquire before execution, or None if no lock needed
        """
        raise NotImplementedError("Subclasses must implement lock_id")

    @classmethod
    @abstractmethod
    def target_statuses(cls) -> list[RouteStatus]:
        """Get the target route statuses for this handler.

        Returns:
            List of route statuses that this handler targets
        """
        raise NotImplementedError("Subclasses must implement target_statuses()")

    @classmethod
    @abstractmethod
    def next_status(cls) -> Optional[RouteStatus]:
        """Get the next route status after this handler's operation.

        Returns:
            The next route status
        """
        raise NotImplementedError("Subclasses must implement next_status()")

    @classmethod
    @abstractmethod
    def failure_status(cls) -> Optional[RouteStatus]:
        """Get the failure route status if applicable.

        Returns:
            The failure route status, or None if not applicable
        """
        raise NotImplementedError("Subclasses must implement failure_status()")

    @abstractmethod
    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute the route operation.

        Returns:
            Result of the route operation
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after the operation.

        Args:
            result: The result from execute()
        """
        raise NotImplementedError("Subclasses must implement post_process()")
