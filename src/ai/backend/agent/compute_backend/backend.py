"""Container/VM-common interface for the instance lifecycle.

The backend owns instances only; side resources (alloc/port/network/scratch) are
acquired/released by separate managers. See proposals/BEP-1057-agent-re-architecture.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.agent.compute_backend.types import (
    InstanceHandle,
    InstanceInfo,
    InstanceSpec,
    InstanceStat,
)


class ComputeBackend(ABC):
    @abstractmethod
    async def create_instance(self, spec: InstanceSpec) -> InstanceHandle:
        raise NotImplementedError

    @abstractmethod
    async def destroy_instance(self, handle: InstanceHandle) -> None:
        """Idempotent: destroying an already-gone instance is a no-op."""
        raise NotImplementedError

    @abstractmethod
    async def inspect_instance(self, handle: InstanceHandle) -> InstanceInfo:
        """Raises InstanceNotFoundError when the instance no longer exists."""
        raise NotImplementedError

    @abstractmethod
    async def list_instances(self) -> Sequence[InstanceInfo]:
        """Each entry is self-described from labels, so kernel correlation survives a restart."""
        raise NotImplementedError

    @abstractmethod
    async def collect_stats(self, handle: InstanceHandle) -> InstanceStat:
        raise NotImplementedError
