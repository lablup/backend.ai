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
    _agent: "AbstractAgent"
    _port_unused_counts: defaultdict[int, int]

    def __init__(
        self,
        agent: "AbstractAgent",
    ) -> None:
        self._agent = agent
        self._port_usage_counts: defaultdict[int, int] = defaultdict(int)
        self._port_unused_counts: defaultdict[int, int] = defaultdict(int)

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

        unused_ports = self._agent.current_port_pool() - occupied_host_ports
        ports_to_remove = set()
        for port in unused_ports:
            self._port_unused_counts[port] += 1
            if self._port_unused_counts[port] >= PORT_USAGE_THRESHOLD:
                ports_to_remove.add(port)
                del self._port_unused_counts[port]
        self._agent.release_unused_ports(ports_to_remove)

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
