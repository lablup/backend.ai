from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.manager.bgtask.tasks.commit_session import CommitSessionHandler
from ai.backend.manager.bgtask.tasks.purge_images import PurgeImagesHandler
from ai.backend.manager.bgtask.tasks.rescan_gpu_alloc_maps import RescanGPUAllocMapsHandler
from ai.backend.manager.bgtask.tasks.rescan_images import RescanImagesHandler
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.services.processors import Processors


@dataclass
class BgtaskRegistryInput:
    """Input required for BackgroundTaskHandlerRegistry setup."""

    processors: Processors
    background_task_manager: BackgroundTaskManager
    repositories: Repositories
    agent_client_pool: AgentClientPool
    agent_registry: AgentRegistry
    event_hub: EventHub
    event_fetcher: EventFetcher


class BgtaskRegistryDependency(
    NonMonitorableDependencyProvider[BgtaskRegistryInput, BackgroundTaskHandlerRegistry]
):
    """Provides BackgroundTaskHandlerRegistry lifecycle management.

    Creates the registry, registers all task handlers, and sets it
    on the BackgroundTaskManager.
    """

    @property
    def stage_name(self) -> str:
        return "bgtask-registry"

    @asynccontextmanager
    async def provide(
        self, setup_input: BgtaskRegistryInput
    ) -> AsyncIterator[BackgroundTaskHandlerRegistry]:
        registry = BackgroundTaskHandlerRegistry()
        registry.register(RescanImagesHandler(setup_input.processors))
        registry.register(PurgeImagesHandler(setup_input.processors))
        registry.register(
            RescanGPUAllocMapsHandler(
                agent_repository=setup_input.repositories.agent.repository,
                agent_client_pool=setup_input.agent_client_pool,
            )
        )
        registry.register(
            CommitSessionHandler(
                session_repository=setup_input.repositories.session.repository,
                image_repository=setup_input.repositories.image.repository,
                agent_registry=setup_input.agent_registry,
                event_hub=setup_input.event_hub,
                event_fetcher=setup_input.event_fetcher,
            )
        )
        setup_input.background_task_manager.set_registry(registry)
        yield registry
