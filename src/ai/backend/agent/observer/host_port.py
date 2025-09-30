import logging
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import ContainerStatus
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ..agent import AbstractAgent


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HostPortObserver(AbstractObserver):
    def __init__(
        self,
        agent: "AbstractAgent",
    ) -> None:
        self._agent = agent

    @property
    @override
    def name(self) -> str:
        return "agent_host_port"

    @override
    async def observe(self) -> None:
        containers = await self._agent.enumerate_containers(ContainerStatus.active_set())

        occupied_host_ports: set[int] = set()
        for _, container in containers:
            for port in container.ports:
                occupied_host_ports.add(port.host_port)
        self._agent.sync_port_pool(occupied_host_ports)

    @override
    def observe_interval(self) -> float:
        return 15.0

    @classmethod
    @override
    def timeout(cls) -> Optional[float]:
        return 10.0

    @override
    async def cleanup(self) -> None:
        pass
