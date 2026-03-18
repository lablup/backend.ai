from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)


@dataclass
class SchedulingControllerInput:
    """Input required for scheduling controller setup."""

    repository: SchedulerRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient
    network_plugin_ctx: NetworkPluginContext
    hook_plugin_ctx: HookPluginContext


class SchedulingControllerDependency(
    NonMonitorableDependencyProvider[SchedulingControllerInput, SchedulingController],
):
    """Provides SchedulingController lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "scheduling-controller"

    @asynccontextmanager
    async def provide(
        self, setup_input: SchedulingControllerInput
    ) -> AsyncIterator[SchedulingController]:
        """Initialize and provide a scheduling controller.

        Args:
            setup_input: Input containing repositories, config, and plugins

        Yields:
            Initialized SchedulingController
        """
        controller = SchedulingController(
            SchedulingControllerArgs(
                repository=setup_input.repository,
                config_provider=setup_input.config_provider,
                storage_manager=setup_input.storage_manager,
                event_producer=setup_input.event_producer,
                valkey_schedule=setup_input.valkey_schedule,
                network_plugin_ctx=setup_input.network_plugin_ctx,
                hook_plugin_ctx=setup_input.hook_plugin_ctx,
            )
        )
        yield controller
