"""The container runtime as a network plugin's privileged helper may see it. See KNOWLEDGE.md."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

__all__ = ("ContainerLocator", "LiveContainer")


@dataclass(frozen=True)
class LiveContainer:
    """A running kernel container, as much of it as the network layer needs."""

    session_id: str
    #: None when the backend does not record one — the container is then nobody's to reclaim.
    owner_agent_id: str | None


class ContainerLocator(ABC):
    """The runtime, as a privileged network helper is allowed to see it."""

    @abstractmethod
    async def open(self) -> None:
        """Connect to the backend; called once before the helper serves."""
        raise NotImplementedError

    async def close(self) -> None:
        """Release whatever ``open`` acquired. Default no-op."""

    @property
    def rootless(self) -> bool:
        """Whether the backend's container records are written by the agent's own (non-root) user."""
        return False

    @abstractmethod
    async def container_pid(self, container_id: str) -> int | None:
        """PID 1 of the container, or None if it is not running."""
        raise NotImplementedError

    @abstractmethod
    async def live_sessions(self) -> Mapping[str, LiveContainer]:
        """``{container_id: LiveContainer}`` for the containers this node runs, from one snapshot."""
        raise NotImplementedError

    def cgroup_path(self, container_id: str) -> Path:
        """Where this container's cgroup lives, for backends that ask a helper to create it.

        Refuses by default.
        """
        raise NotImplementedError(
            f"{type(self).__name__} places its own cgroups; a helper must not create one"
        )
