from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager, BackgroundTaskManagerArgs
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.storage.bgtask.registry import BgtaskHandlerRegistryCreator
from ai.backend.storage.volumes.pool import VolumePool


@dataclass
class BackgroundTaskManagerInput:
    """Input required for the background task manager setup."""

    event_producer: EventProducer
    valkey_bgtask: ValkeyBgtaskClient
    volume_pool: VolumePool
    server_id: str


class BackgroundTaskManagerProvider(
    NonMonitorableDependencyProvider[BackgroundTaskManagerInput, BackgroundTaskManager]
):
    """Provider for the background task manager."""

    @property
    @override
    def stage_name(self) -> str:
        return "background-task-manager"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: BackgroundTaskManagerInput
    ) -> AsyncIterator[BackgroundTaskManager]:
        registry_creator = BgtaskHandlerRegistryCreator(
            setup_input.volume_pool,
            setup_input.event_producer,
        )
        manager = BackgroundTaskManager(
            BackgroundTaskManagerArgs(
                event_producer=setup_input.event_producer,
                task_registry=registry_creator.create(),
                valkey_client=setup_input.valkey_bgtask,
                server_id=setup_input.server_id,
            )
        )
        await manager.init()
        try:
            yield manager
        finally:
            await manager.shutdown()
