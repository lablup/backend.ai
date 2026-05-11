"""Base class for route lifecycle handlers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.manager.data.deployment.types import (
    RouteHandlerCategory,
    RouteStatusTransitions,
    RouteTargetStatuses,
)
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


class RouteHandler(ABC):
    """Base class for route operation handlers.

    Routes are classified by two axes:
    - lifecycle status (PROVISIONING, RUNNING, TERMINATING, ...)
    - health status (NOT_CHECKED, HEALTHY, UNHEALTHY, DEGRADED)

    Each handler declares which (lifecycle, health) combinations it targets
    via target_statuses().
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @classmethod
    @abstractmethod
    def category(cls) -> RouteHandlerCategory:
        """Whether this handler manages lifecycle or health transitions."""
        raise NotImplementedError("Subclasses must implement category()")

    @property
    @abstractmethod
    def lock_id(self) -> LockID | None:
        """Get the lock ID for this handler."""
        raise NotImplementedError("Subclasses must implement lock_id")

    @classmethod
    @abstractmethod
    def target_statuses(cls) -> RouteTargetStatuses:
        """Lifecycle and health statuses this handler targets."""
        raise NotImplementedError("Subclasses must implement target_statuses()")

    @classmethod
    @abstractmethod
    def status_transitions(cls) -> RouteStatusTransitions:
        """Define state transitions for different handler outcomes.

        Returns:
            RouteStatusTransitions with RouteTransitionTarget for each outcome.
            Each target can change lifecycle status, health status, or both.
        """
        raise NotImplementedError("Subclasses must implement status_transitions()")

    @abstractmethod
    async def execute(self, routes: Sequence[RouteData]) -> RouteExecutionResult:
        """Execute the route operation."""
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: RouteExecutionResult) -> None:
        """Handle post-processing after the operation."""
        raise NotImplementedError("Subclasses must implement post_process()")
