import logging

import sqlalchemy as sa

from ai.backend.common.events.agent import (
    AgentHeartbeatEvent,
    AgentImagesRemoveEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.types import (
    AgentId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import InstanceNotFound
from ai.backend.manager.registry import AgentRegistry

from ..models.agent import AgentStatus, agents
from ..models.utils import (
    ExtendedAsyncSAEngine,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentEventHandler:
    def __init__(self, registry: AgentRegistry, db: ExtendedAsyncSAEngine) -> None:
        self._registry = registry
        self._db = db

    async def handle_agent_started(
        self,
        context: None,
        source: AgentId,
        event: AgentStartedEvent,
    ) -> None:
        log.info("instance_lifecycle: ag:{0} joined (via event, {1})", source, event.reason)
        await self._registry.update_instance(
            source,
            {
                "status": AgentStatus.ALIVE,
            },
        )

    async def handle_agent_terminated(
        self,
        context: None,
        source: AgentId,
        event: AgentTerminatedEvent,
    ) -> None:
        if event.reason == "agent-lost":
            await self._registry.mark_agent_terminated(source, AgentStatus.LOST)
            self._registry.agent_cache.discard(source)
        elif event.reason == "agent-restart":
            log.info("agent@{0} restarting for maintenance.", source)
            await self._registry.update_instance(
                source,
                {
                    "status": AgentStatus.RESTARTING,
                },
            )
        else:
            # On normal instance termination, kernel_terminated events were already
            # triggered by the agent.
            await self._registry.mark_agent_terminated(source, AgentStatus.TERMINATED)
            self._registry.agent_cache.discard(source)

    async def handle_agent_heartbeat(
        self,
        context: None,
        source: AgentId,
        event: AgentHeartbeatEvent,
    ) -> None:
        await self._registry.handle_heartbeat(source, event.agent_info)

    async def handle_agent_images_remove(
        self,
        context: None,
        source: AgentId,
        event: AgentImagesRemoveEvent,
    ) -> None:
        await self._registry.handle_agent_images_remove(source, event.image_canonicals)

    async def handle_check_agent_resource(
        self, context: None, source: AgentId, event: DoAgentResourceCheckEvent
    ) -> None:
        async with self._db.begin_readonly() as conn:
            query = (
                sa.select([agents.c.occupied_slots])
                .select_from(agents)
                .where(agents.c.id == source)
            )
            result = await conn.execute(query)
            row = result.first()
            if not row:
                raise InstanceNotFound(source)
            log.info("agent@{0} occupied slots: {1}", source, row["occupied_slots"].to_json())
