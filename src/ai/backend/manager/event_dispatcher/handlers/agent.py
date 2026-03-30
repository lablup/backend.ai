import asyncio
import logging
from collections.abc import Callable

import sqlalchemy as sa

from ai.backend.common.events.event_types.agent.anycast import (
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentImagesRemoveEvent,
    AgentInstalledImagesRemoveEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.exception import ProcessorNotReadyError
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.resource import InstanceNotFound
from ai.backend.manager.models.agent import AgentStatus, agents
from ai.backend.manager.models.resource_slot import AgentResourceRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.agent.actions.handle_heartbeat import HandleHeartbeatAction
from ai.backend.manager.services.agent.actions.mark_agent_exit import MarkAgentExitAction
from ai.backend.manager.services.agent.actions.mark_agent_running import MarkAgentRunningAction
from ai.backend.manager.services.agent.actions.remove_agent_from_images import (
    RemoveAgentFromImagesAction,
)
from ai.backend.manager.services.agent.actions.remove_agent_from_images_by_canonicals import (
    RemoveAgentFromImagesByCanonicalsAction,
)
from ai.backend.manager.services.processors import Processors

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentEventHandler:
    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine
    _event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    _processor_factory: Callable[[], Processors]
    _processors: Processors | None

    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        event_dispatcher_plugin_ctx: EventDispatcherPluginContext,
        processors_factory: Callable[[], Processors],
    ) -> None:
        self._registry = registry
        self._db = db
        self._event_dispatcher_plugin_ctx = event_dispatcher_plugin_ctx
        self._processors = None
        self._processor_factory = processors_factory

    # Lazy initialization of processors as AgentEventHandler is created earlier than Processors
    async def get_processors(self) -> Processors:
        if self._processors is None:
            for _ in range(5):
                try:
                    self._processors = self._processor_factory()
                    return self._processors
                except Exception:
                    await asyncio.sleep(0.1)
        if self._processors is None:
            log.error("Agent processors not ready after multiple attempts.")
            raise ProcessorNotReadyError("Agent processors not ready. Try again after a while.")
        return self._processors

    async def handle_agent_started(
        self,
        _context: None,
        source: AgentId,
        event: AgentStartedEvent,
    ) -> None:
        log.info("instance_lifecycle: ag:{0} joined (via event, {1})", source, event.reason)
        processors = await self.get_processors()
        await processors.agent.mark_agent_running.wait_for_complete(
            MarkAgentRunningAction(
                agent_id=source,
                agent_status=AgentStatus.ALIVE,
            )
        )

    async def handle_agent_terminated(
        self,
        _context: None,
        source: AgentId,
        event: AgentTerminatedEvent,
    ) -> None:
        processors = await self.get_processors()
        if event.reason == "agent-lost":
            await processors.agent.mark_agent_exit.wait_for_complete(
                MarkAgentExitAction(
                    agent_id=source,
                    agent_status=AgentStatus.LOST,
                )
            )
        elif event.reason == "agent-restart":
            log.info("agent@{0} restarting for maintenance.", source)
            await processors.agent.mark_agent_running.wait_for_complete(
                MarkAgentRunningAction(
                    agent_id=source,
                    agent_status=AgentStatus.RESTARTING,
                )
            )
        else:
            # On normal instance termination, kernel_terminated events were already
            # triggered by the agent.
            await processors.agent.mark_agent_exit.wait_for_complete(
                MarkAgentExitAction(
                    agent_id=source,
                    agent_status=AgentStatus.TERMINATED,
                )
            )

    async def handle_agent_heartbeat(
        self,
        _context: None,
        source: AgentId,
        event: AgentHeartbeatEvent,
    ) -> None:
        processor = await self.get_processors()
        await processor.agent.handle_heartbeat.wait_for_complete(
            action=HandleHeartbeatAction(agent_id=source, agent_info=event.agent_info)
        )

    # For compatibility with redis key made with image canonical strings
    # Use remove_agent_from_images_by_id instead of this if possible
    async def handle_agent_images_remove(
        self,
        _context: None,
        source: AgentId,
        event: AgentImagesRemoveEvent,
    ) -> None:
        processor = await self.get_processors()
        await processor.agent.remove_agent_from_images_by_canonicals.wait_for_complete(
            action=RemoveAgentFromImagesByCanonicalsAction(
                agent_id=source, image_canonicals=event.image_canonicals
            )
        )

    async def handle_agent_installed_images_remove(
        self,
        _context: None,
        source: AgentId,
        event: AgentInstalledImagesRemoveEvent,
    ) -> None:
        processor = await self.get_processors()
        await processor.agent.remove_agent_from_images.wait_for_complete(
            action=RemoveAgentFromImagesAction(
                agent_id=source, scanned_images=dict(event.scanned_images)
            )
        )

    async def handle_check_agent_resource(
        self, _context: None, source: AgentId, _event: DoAgentResourceCheckEvent
    ) -> None:
        async with self._db.begin_readonly() as conn:
            # Check agent existence
            agent_query = sa.select(sa.literal(1)).select_from(agents).where(agents.c.id == source)
            agent_result = await conn.execute(agent_query)
            if agent_result.first() is None:
                raise InstanceNotFound(source)
            # Read used slots from normalized agent_resources table
            ar = AgentResourceRow.__table__
            query = sa.select(ar.c.slot_name, ar.c.used).where(ar.c.agent_id == source)
            result = await conn.execute(query)
            used_slots = {row.slot_name: row.used for row in result}
            log.info("agent@{0} used slots: {1}", source, used_slots)

    async def handle_agent_error(
        self,
        context: None,
        source: AgentId,
        event: AgentErrorEvent,
    ) -> None:
        await self._event_dispatcher_plugin_ctx.handle_event(context, source, event)
