import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import ContainerStatus
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ..agent import AbstractAgent


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


PORT_USAGE_THRESHOLD = 4


class HostPortObserver(AbstractObserver):
    _agent: "AbstractAgent"
    _port_unused_counts: defaultdict[int, int]

    def __init__(
        self,
        agent: "AbstractAgent",
    ) -> None:
        self._agent = agent
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

        unused_ports = self._agent.current_used_port_set() - occupied_host_ports
        for previous_unused_port in list(self._port_unused_counts.keys()):
            if previous_unused_port not in unused_ports:
                del self._port_unused_counts[previous_unused_port]

        ports_to_release = set()
        for unused_port in unused_ports:
            self._port_unused_counts[unused_port] += 1
            if self._port_unused_counts[unused_port] >= PORT_USAGE_THRESHOLD:
                ports_to_release.add(unused_port)
                del self._port_unused_counts[unused_port]
        self._agent.release_unused_ports(ports_to_release)

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
