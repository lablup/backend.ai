import logging
from collections.abc import Collection, Iterable

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
    ContainerKernelId,
    KernelContainerId,
    KernelId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import InstanceNotFound
from ai.backend.manager.registry import AgentRegistry

from ...models.agent import AgentStatus, agents
from ...models.kernel import (
    ConditionMerger,
    KernelRow,
    by_kernel_ids,
)
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

    def _filter_containers_to_purge(
        self,
        active_containers: Iterable[ContainerKernelId],
        kernel_should_alive: Collection[KernelId],
    ) -> list[ContainerKernelId]:
        """
        Helper function to filter containers that should be purged based on the
        provided kernel status.
        """
        containers_to_purge: list[ContainerKernelId] = []
        for container in active_containers:
            if container.kernel_id not in kernel_should_alive:
                containers_to_purge.append(container)
        return containers_to_purge

    def _filter_kernels_to_clean(
        self,
        active_kernels: Iterable[KernelContainerId],
        kernel_should_alive: Collection[KernelId],
    ) -> list[KernelId]:
        """
        Helper function to filter kernels that should be cleaned based on the
        provided kernel status.
        """
        kernels_to_clean: set[KernelId] = set()
        for kernel_container_id in active_kernels:
            kernel_id = kernel_container_id.kernel_id
            if kernel_id not in kernel_should_alive:
                kernels_to_clean.add(kernel_id)
        return list(kernels_to_clean)

    async def handle_agent_container_heartbeat(
        self,
        context: None,
        source: AgentId,
        event: AgentStatusHeartbeat,
    ) -> None:
        # Do not query Agent id from the event because Agent id can change
        # during the lifetime of the agent, e.g. when it is restarted.
        all_kernel_ids: set[KernelId] = {k.kernel_id for k in event.active_kernels} | {
            c.kernel_id for c in event.active_containers
        }
        kernel_condition = by_kernel_ids(
            all_kernel_ids,
            ConditionMerger.AND,
        )
        kernel_rows = await KernelRow.get_kernels(
            [kernel_condition],
            db=self._db,
        )
        kernel_should_alive: set[KernelId] = {
            kernel_row.id for kernel_row in kernel_rows if kernel_row.status.have_container()
        }
        active_container_ids = [
            ContainerKernelId(cont.container_id, cont.kernel_id) for cont in event.active_containers
        ]
        containers_to_purge = self._filter_containers_to_purge(
            active_container_ids, kernel_should_alive
        )
        active_kernel_ids = event.active_kernels
        kernels_to_clean = self._filter_kernels_to_clean(active_kernel_ids, kernel_should_alive)

        log.debug(
            "agent@{0} heartbeat: Detected {1} dangling containers, {2} dangling kernel registries",
            event.agent_id,
            len(containers_to_purge),
            len(kernels_to_clean),
        )
        if containers_to_purge:
            log.warning(
                "agent@{0} heartbeat: Purging containers: {1}",
                event.agent_id,
                ", ".join(c.human_readable_container_id for c in containers_to_purge),
            )
            await self._registry.purge_containers(
                event.agent_id,
                containers_to_purge,
            )
        if kernels_to_clean:
            log.warning(
                "agent@{0} heartbeat: Cleaning kernels: {1}",
                event.agent_id,
                ", ".join(str(k) for k in kernels_to_clean),
            )
            await self._registry.drop_kernel_registry(
                event.agent_id,
                kernels_to_clean,
            )
