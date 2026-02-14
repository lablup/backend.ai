from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.bgtask.hooks.metric_hook import BackgroundTaskObserver
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer


@dataclass
class BackgroundTaskManagerInput:
    """Input required for background task manager setup."""

    event_producer: EventProducer
    valkey_bgtask: ValkeyBgtaskClient
    server_id: str
    bgtask_observer: BackgroundTaskObserver | None


class BackgroundTaskManagerDependency(
    NonMonitorableDependencyProvider[BackgroundTaskManagerInput, BackgroundTaskManager],
):
    """Provides BackgroundTaskManager with managed lifecycle."""

    @property
    def stage_name(self) -> str:
        return "background-task-manager"

    @asynccontextmanager
    async def provide(
        self, setup_input: BackgroundTaskManagerInput
    ) -> AsyncIterator[BackgroundTaskManager]:
        manager = BackgroundTaskManager(
            setup_input.event_producer,
            valkey_client=setup_input.valkey_bgtask,
            server_id=setup_input.server_id,
            bgtask_observer=setup_input.bgtask_observer,
        )
        try:
            yield manager
        finally:
            await manager.shutdown()
