import logging

import sqlalchemy as sa

from ai.backend.common.events.event_types.agent.anycast import (
    AgentErrorEvent,
    AgentHeartbeatEvent,
    AgentImagesRemoveEvent,
    AgentStartedEvent,
    AgentStatusHeartbeat,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import (
    AgentId,
    KernelContainerId,
    KernelId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import InstanceNotFound
from ai.backend.manager.registry import AgentRegistry

from ...models.agent import AgentStatus, agents
from ...models.kernel import ConditionMerger, KernelRow, KernelStatus, by_agent_id, by_status
from ...models.utils import (
    ExtendedAsyncSAEngine,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentEventHandler:
    def __init__(
        self,
        registry: AgentRegistry,
        db: ExtendedAsyncSAEngine,
        event_dispatcher_plugin_ctx: EventDispatcherPluginContext,
    ) -> None:
        self._registry = registry
        self._db = db
        self._event_dispatcher_plugin_ctx = event_dispatcher_plugin_ctx

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

    async def handle_agent_error(
        self,
        context: None,
        source: AgentId,
        event: AgentErrorEvent,
    ) -> None:
        await self._event_dispatcher_plugin_ctx.handle_event(context, source, event)

    async def handle_agent_container_heartbeat(
        self,
        context: None,
        source: AgentId,
        event: AgentStatusHeartbeat,
    ) -> None:
        status_condition = by_status(KernelStatus.with_containers(), ConditionMerger.AND)
        agent_condition = by_agent_id(event.agent_id, ConditionMerger.AND)
        kernel_rows = await KernelRow.get_kernels(
            [
                status_condition,
                agent_condition,
            ],
            db=self._db,
        )
        kernel_should_alive: set[KernelId] = {kernel_row.id for kernel_row in kernel_rows}

        containers_to_purge: list[KernelContainerId] = []
        kernels_to_clean: set[KernelId] = set()
        for container in event.containers:
            if container.kernel_id not in kernel_should_alive:
                containers_to_purge.append(
                    KernelContainerId(container.kernel_id, container.container_id)
                )

        kernel_ids_of_living_containers: set[KernelId] = {
            container.kernel_id for container in event.containers
        }
        for kernel_id in event.kernel_registry:
            if kernel_id not in kernel_should_alive:
                kernels_to_clean.add(kernel_id)
            if kernel_id not in kernel_ids_of_living_containers:
                kernels_to_clean.add(kernel_id)

        log.info(
            "agent@{0} heartbeat: {1} dangling containers, {2} dangling kernel registries",
            event.agent_id,
            len(containers_to_purge),
            len(kernels_to_clean),
        )
        if containers_to_purge:
            await self._registry.purge_containers(
                event.agent_id,
                containers_to_purge,
            )
        if kernels_to_clean:
            await self._registry.drop_kernel_registry(
                event.agent_id,
                kernels_to_clean,
            )
