import logging
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import (
    AgentStatusHeartbeat,
    ContainerStatusData,
)
from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import ContainerStatus
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ..agent import AbstractAgent


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HeartbeatObserver(AbstractObserver):
    def __init__(
        self,
        agent: "AbstractAgent",
        event_producer: EventProducer,
    ) -> None:
        self._agent = agent
        self._event_producer = event_producer

    @property
    @override
    def name(cls) -> str:
        return "agent_hearbeat"

    @override
    async def observe(self) -> None:
        containers = await self._agent.enumerate_containers(frozenset([ContainerStatus.RUNNING]))
        container_data = [
            ContainerStatusData(
                container.id,
                kernel_id,
                container.status,
            )
            for kernel_id, container in containers
        ]
        await self._event_producer.anycast_event(
            AgentStatusHeartbeat(
                self._agent.id,
                container_data,
            ),
        )

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
