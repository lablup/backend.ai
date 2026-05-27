"""Base classes for periodic task runners (cron) and the tasks they run."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PeriodicTask(ABC):
    """Abstract base class for a unit of work executed periodically by a cron runner."""

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

    @property
    def run_timeout(self) -> float | None:
        """
        Per-execution timeout in seconds.

        When set, a single ``run()`` invocation that exceeds this duration is
        cancelled so it cannot block subsequent ticks (e.g. a hanging Redis call).
        ``None`` (default) means no per-execution timeout.
        """
        return None


class Cron(ABC):
    """
    Abstract interface for periodic task runners with a start/stop lifecycle.

    A cron owns a set of :class:`PeriodicTask` instances and drives them on their
    individual intervals until stopped.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start the cron and begin running its tasks."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Stop the cron and all of its tasks."""
        raise NotImplementedError
