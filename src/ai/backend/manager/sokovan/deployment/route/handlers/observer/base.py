"""Base class for route observers.

Route observers collect data from routes without changing their state.
This mirrors the KernelObserver pattern used in the session scheduler.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.manager.repositories.deployment.types import RouteData


@dataclass
class RouteObservationResult:
    """Result of route observation."""

    observed_count: int


class RouteObserver(ABC):
    """Base class for route observation without state transitions.

    Unlike RouteHandler which transitions route states,
    RouteObserver only observes and collects data from routes.
    No DB status changes are applied.
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the observer for logging."""
        raise NotImplementedError

    @abstractmethod
    async def observe(self, routes: Sequence[RouteData]) -> RouteObservationResult:
        """Observe the given routes without changing their state.

        Args:
            routes: Routes to observe

        Returns:
            RouteObservationResult containing observed count
        """
        raise NotImplementedError
