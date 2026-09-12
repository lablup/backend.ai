from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, override

from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import ContainerStatus
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


PORT_USAGE_THRESHOLD = 4


class HostPortObserver(AbstractObserver):
    _agent: AbstractAgent[Any, Any]
    _port_unused_counts: defaultdict[int, int]

    def __init__(
        self,
        agent: AbstractAgent[Any, Any],
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
        # And the ports this agent published itself. A session-networked kernel runs with
        # `NetworkMode: none` and is reached only through the DNAT rules the agent installs, so
        # Docker publishes nothing for it and `container.ports` is empty -- every one of its live
        # host ports read as unused here and was handed to the next kernel, whose own DNAT rule
        # then lost to the older one still in PREROUTING.
        occupied_host_ports |= await self._published_host_ports()

        port_pool = self._agent.port_pool
        unused_ports = port_pool.used_ports() - occupied_host_ports
        for previous_unused_port in list(self._port_unused_counts.keys()):
            if previous_unused_port not in unused_ports:
                del self._port_unused_counts[previous_unused_port]

        ports_to_release: set[int] = set()
        for unused_port in unused_ports:
            self._port_unused_counts[unused_port] += 1
            if self._port_unused_counts[unused_port] >= PORT_USAGE_THRESHOLD:
                ports_to_release.add(unused_port)
                del self._port_unused_counts[unused_port]
        if ports_to_release:
            log.info(
                "releasing unused ports back to port pool. "
                "current port-pool length: {}, releasing length: {}",
                len(port_pool),
                len(ports_to_release),
            )
            port_pool.release_many(ports_to_release)

    async def _published_host_ports(self) -> set[int]:
        """Host ports held by this agent's own DNAT rules, or an empty set if they cannot be read.

        Empty on failure is safe here only because releasing needs `PORT_USAGE_THRESHOLD`
        consecutive observations: one unreadable pass cannot release anything on its own.
        """
        publisher = self._agent.port_publisher()
        if publisher is None:
            return set()
        try:
            return {forward.host_port for forward in await publisher.list_forwards()}
        except Exception:
            log.exception("could not read this node's published ports; not counting them as used")
            return set()

    @override
    def observe_interval(self) -> float:
        return 15.0

    @classmethod
    @override
    def timeout(cls) -> float | None:
        return 10.0

    @override
    async def cleanup(self) -> None:
        pass
