"""Base classes for periodic tasks."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PeriodicTask(ABC):
    """Abstract base class for tasks that execute periodically when leader."""

    @abstractmethod
    async def run(self) -> None:
        """Execute the task."""
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Task name for logging and identification."""
        raise NotImplementedError

    @property
    @abstractmethod
    def interval(self) -> float:
        """Interval between task executions in seconds."""
        raise NotImplementedError

    @property
    @abstractmethod
    def initial_delay(self) -> float:
        """Initial delay before first execution in seconds."""
        raise NotImplementedError
