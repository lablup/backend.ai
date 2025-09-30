import asyncio
import logging
from collections.abc import Collection, Iterable
from typing import Callable, Optional

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
from ai.backend.common.exception import ProcessorNotReadyError
from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.common.types import (
    AgentId,
    ContainerKernelId,
    KernelContainerId,
    KernelId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.resource import InstanceNotFound
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.services.agent.actions.handle_heartbeat import HandleHeartbeatAction
from ai.backend.manager.services.agent.actions.mark_agent_exit import MarkAgentExitAction
from ai.backend.manager.services.agent.actions.mark_agent_running import MarkAgentRunningAction
from ai.backend.manager.services.agent.actions.remove_agent_from_images import (
    RemoveAgentFromImagesAction,
)
from ai.backend.manager.services.processors import Processors

from ...models.agent import AgentStatus, agents
from ...models.kernel import (
    KernelRow,
    by_kernel_ids,
)
from ...models.utils import (
    ExtendedAsyncSAEngine,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentEventHandler:
    _registry: AgentRegistry
    _db: ExtendedAsyncSAEngine
    _event_dispatcher_plugin_ctx: EventDispatcherPluginContext
    _processor_factory: Callable[[], Processors]
    _processors: Optional[Processors]

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
        context: None,
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
        context: None,
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
        context: None,
        source: AgentId,
        event: AgentHeartbeatEvent,
    ) -> None:
        processor = await self.get_processors()
        await processor.agent.handle_heartbeat.wait_for_complete(
            action=HandleHeartbeatAction(agent_id=source, agent_info=event.agent_info)
        )

    async def handle_agent_images_remove(
        self,
        context: None,
        source: AgentId,
        event: AgentImagesRemoveEvent,
    ) -> None:
        processor = await self.get_processors()
        await processor.agent.remove_agent_from_images.wait_for_complete(
            action=RemoveAgentFromImagesAction(
                agent_id=source, image_canonicals=event.image_canonicals
            )
        )

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
        kernel_rows = await KernelRow.get_kernels(
            [by_kernel_ids(all_kernel_ids)],
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
