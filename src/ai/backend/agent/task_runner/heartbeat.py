import logging
from collections.abc import Awaitable, Sequence
from typing import Callable, Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import (
    AgentStatusHeartbeat,
    ContainerStatusData,
)
from ai.backend.common.types import AgentId, ContainerStatus, KernelId
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import (
    Container,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HeartbeatTask:
    def __init__(
        self,
        agent_id: AgentId,
        container_enumerator: Callable[
            [frozenset[ContainerStatus]], Awaitable[Sequence[tuple[KernelId, Container]]]
        ],
        event_producer: EventProducer,
    ) -> None:
        self._agent_id = agent_id
        self._container_enumerator = container_enumerator
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        return "agent_hearbeat"

    @classmethod
    def timeout(cls) -> Optional[float]:
        return 10.0

    async def run(self, resource: None) -> None:
        containers = await self._container_enumerator(frozenset([ContainerStatus.RUNNING]))
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
                self._agent_id,
                container_data,
            ),
        )

    async def setup(self) -> None:
        pass

    async def teardown(self, resource: None) -> None:
        pass
