import logging
from datetime import datetime

import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import (
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentImagesRemoveEvent,
    AgentInstalledImagesRemoveEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.agent.types import AgentHeartbeatUpsert
from ai.backend.manager.errors.resource import InstanceNotFound
from ai.backend.manager.models.agent import AgentStatus, agents
from ai.backend.manager.models.agent.updaters import AgentExitStatusUpdater, AgentStatusUpdater
from ai.backend.manager.models.resource_slot import AgentResourceRow
from ai.backend.manager.models.utils import (
    ExtendedAsyncSAEngine,
)
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.types import OptionalState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentEventHandler:
    """Applies agent lifecycle events to the agent repository.

    These transitions carry no caller and no permission, so they take the repository
    directly rather than an action; the service layer answers for API calls only.
    """

    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine
    _event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    _agent_repository: AgentRepository
    _event_producer: EventProducer

    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        event_dispatcher_plugin_ctx: EventDispatcherPluginContext,
        agent_repository: AgentRepository,
        event_producer: EventProducer,
    ) -> None:
        self._registry = registry
        self._db = db
        self._event_dispatcher_plugin_ctx = event_dispatcher_plugin_ctx
        self._agent_repository = agent_repository
        self._event_producer = event_producer

    async def _mark_agent_running(self, agent_id: AgentId, status: AgentStatus) -> None:
        agent_uuid = await self._agent_repository.lookup_uuid(agent_id)
        if agent_uuid is None:
            log.warning("agent {0} is not registered; skipping the status write.", agent_id)
            return
        await self._agent_repository.update_agent_status(
            AgentStatusUpdater(
                agent_uuid=agent_uuid,
                status=status,
                status_changed=datetime.now(tzutc()),
            )
        )

    async def _mark_agent_exit(self, agent_id: AgentId, status: AgentStatus) -> None:
        agent_uuid = await self._agent_repository.lookup_uuid(agent_id)
        if agent_uuid is not None:
            now = datetime.now(tzutc())
            written = await self._agent_repository.mark_agent_exit(
                AgentExitStatusUpdater(
                    agent_uuid=agent_uuid,
                    status=status,
                    status_changed=now,
                    lost_at=OptionalState.update(now),
                )
            )
            if written is not None:
                match status:
                    case AgentStatus.LOST:
                        log.warning("agent {0} heartbeat timeout detected.", agent_id)
                    case AgentStatus.TERMINATED:
                        log.info("agent {0} has terminated.", agent_id)
                    case _:
                        pass
        await self._agent_repository.cleanup_agent_caches(agent_id)
        self._registry.agent_cache.discard(agent_id)

    async def handle_agent_started(
        self,
        _context: None,
        source: AgentId,
        event: AgentStartedEvent,
    ) -> None:
        log.info("instance_lifecycle: ag:{0} joined (via event, {1})", source, event.reason)
        await self._mark_agent_running(source, AgentStatus.ALIVE)

    async def handle_agent_terminated(
        self,
        _context: None,
        source: AgentId,
        event: AgentTerminatedEvent,
    ) -> None:
        if event.reason == "agent-lost":
            await self._mark_agent_exit(source, AgentStatus.LOST)
        elif event.reason == "agent-restart":
            log.info("agent@{0} restarting for maintenance.", source)
            await self._mark_agent_running(source, AgentStatus.RESTARTING)
        else:
            # On normal instance termination, kernel_terminated events were already
            # triggered by the agent.
            await self._mark_agent_exit(source, AgentStatus.TERMINATED)

    async def handle_agent_heartbeat(
        self,
        _context: None,
        source: AgentId,
        event: AgentHeartbeatEvent,
    ) -> None:
        agent_info = event.agent_info
        upsert_data = AgentHeartbeatUpsert.from_agent_info(
            agent_id=source,
            agent_info=agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )
        result = await self._agent_repository.sync_agent_heartbeat(source, upsert_data)
        self._registry.agent_cache.update(source, agent_info.addr, agent_info.public_key)
        if result.was_revived:
            await self._event_producer.anycast_event(
                AgentStartedEvent(reason="revived"), source_override=source
            )
        await self._agent_repository.sync_installed_images(agent_id=source)
        await self._registry.hook_plugin_ctx.notify(
            "POST_AGENT_HEARTBEAT",
            (source, agent_info.scaling_group, agent_info.available_resource_slots),
        )

    # For compatibility with redis key made with image canonical strings
    # Use remove_agent_from_images_by_id instead of this if possible
    async def handle_agent_images_remove(
        self,
        _context: None,
        source: AgentId,
        event: AgentImagesRemoveEvent,
    ) -> None:
        await self._agent_repository.remove_agent_from_images_by_canonicals(
            source, event.image_canonicals
        )

    async def handle_agent_installed_images_remove(
        self,
        _context: None,
        source: AgentId,
        event: AgentInstalledImagesRemoveEvent,
    ) -> None:
        await self._agent_repository.remove_agent_from_images(source, dict(event.scanned_images))

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
