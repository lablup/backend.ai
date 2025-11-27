from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import ContainerStatus, KernelId
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ..agent import AbstractAgent


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelPresenceObserver(AbstractObserver):
    """
    Observer that periodically reports kernel presence status to Redis.

    This observer enumerates active containers and updates their presence
    status in Redis using ValkeyScheduleClient. The Manager can then check
    these statuses to detect unhealthy kernels.
    """

    def __init__(
        self,
        agent: AbstractAgent,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> None:
        self._agent = agent
        self._valkey_schedule_client = valkey_schedule_client

    @property
    @override
    def name(self) -> str:
        return "kernel_presence"

    @override
    async def observe(self) -> None:
        containers = await self._agent.enumerate_containers(ContainerStatus.active_set())

        # Only report RUNNING containers as healthy
        # Non-RUNNING containers will naturally become STALE (no updates)
        kernel_presences: dict[KernelId, bool] = {
            kernel_id: True
            for kernel_id, container in containers
            if container.status == ContainerStatus.RUNNING
        }

        if kernel_presences:
            await self._valkey_schedule_client.update_kernel_presence_batch(kernel_presences)

    @override
    def observe_interval(self) -> float:
        return 60.0

    @classmethod
    @override
    def timeout(cls) -> Optional[float]:
        return 10.0

    @override
    async def cleanup(self) -> None:
        pass
