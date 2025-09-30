import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import ContainerStatus
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ..agent import AbstractAgent


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


PORT_USAGE_THRESHOLD = 2


class HostPortObserver(AbstractObserver):
    def __init__(
        self,
        agent: "AbstractAgent",
    ) -> None:
        self._agent = agent
        self._port_usage_counts: defaultdict[int, int] = defaultdict(int)

    @property
    @override
    def name(self) -> str:
        return "agent_host_port"

    @override
    async def observe(self) -> None:
        containers = await self._agent.enumerate_containers(ContainerStatus.active_set())

        occupied_host_ports: set[int] = set()
        for _, container in containers:
            for container_port in container.ports:
                occupied_host_ports.add(container_port.host_port)

        confirmed_occupied_ports: set[int] = set()
        for port in self._port_usage_counts:
            if port not in occupied_host_ports:
                self._port_usage_counts[port] = 0

        for port in occupied_host_ports:
            self._port_usage_counts[port] += 1
            if self._port_usage_counts[port] >= PORT_USAGE_THRESHOLD:
                confirmed_occupied_ports.add(port)
                # Set the value to 1 to avoid overflow in long-running agents
                self._port_usage_counts[port] = 1
        self._agent.reset_port_pool(confirmed_occupied_ports)

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
