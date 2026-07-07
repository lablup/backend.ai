"""Container/VM-common interface for the instance lifecycle.

The backend owns instances only; side resources (alloc/port/network/scratch) are
acquired/released by separate managers. `destroy_instance` triggers instance
teardown alone — the upper orchestration layer releases side resources in
acquisition-reverse order. See proposals/BEP-1057-agent-re-architecture.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.agent.compute_backend.instance import ComputeInstance
from ai.backend.agent.compute_backend.types import InstanceId, InstanceSpec


class ComputeBackend(ABC):
    @abstractmethod
    async def create_instance(self, spec: InstanceSpec) -> ComputeInstance:
        raise NotImplementedError

    @abstractmethod
    async def destroy_instance(self, instance_id: InstanceId) -> None:
        """Trigger instance teardown only; idempotent. Side resources are released elsewhere."""
        raise NotImplementedError

    @abstractmethod
    async def load_instance(self, instance_id: InstanceId) -> ComputeInstance:
        """Raises InstanceNotFoundError when the instance no longer exists."""
        raise NotImplementedError

    @abstractmethod
    async def list_instances(self) -> Sequence[ComputeInstance]:
        """Instances the backend currently tracks."""
        raise NotImplementedError

    @abstractmethod
    async def recover(self) -> None:
        """Rebuild the tracked set from substrate ground truth (labels) after registry loss.

        A command: the recovered instances are read back via `list_instances`.
        """
        raise NotImplementedError
