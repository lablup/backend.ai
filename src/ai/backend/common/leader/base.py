"""Abstract base classes for leader election."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol


class LeadershipChecker(Protocol):
    """Protocol for checking leadership status."""

    @property
    def is_leader(self) -> bool:
        """Check if this instance is currently the leader."""
        ...


class LeaderTask(ABC):
    """
    Abstract base class for tasks that should run only on the leader instance.
    These are registered with ValkeyLeaderElection.
    """

    @abstractmethod
    async def start(self, leadership_checker: LeadershipChecker) -> None:
        """
        Start the leader task.

        Args:
            leadership_checker: Object that provides leadership status
        """
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Stop the leader task."""
        raise NotImplementedError


class AbstractLeaderElection(ABC):
    """
    Abstract base class for leader election implementations.

    Defines the interface that all leader election implementations must follow.
    """

    @property
    @abstractmethod
    def is_leader(self) -> bool:
        """Check if this instance is currently the leader."""
        raise NotImplementedError

    @property
    @abstractmethod
    def server_id(self) -> str:
        """Get the server ID."""
        raise NotImplementedError

    @abstractmethod
    def register_task(self, task: LeaderTask) -> None:
        """
        Register a task to run when this instance is the leader.

        Args:
            task: Leader task to register
        """
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        """Start the leader election process and all registered tasks."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Stop the leader election, all tasks, and release leadership if held."""
        raise NotImplementedError
