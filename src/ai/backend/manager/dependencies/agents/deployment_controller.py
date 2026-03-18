from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)


@dataclass
class DeploymentControllerInput:
    """Input required for deployment controller setup."""

    scheduling_controller: SchedulingController
    deployment_repository: DeploymentRepository
    config_provider: ManagerConfigProvider
    storage_manager: StorageSessionManager
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient
    revision_generator_registry: RevisionGeneratorRegistry


class DeploymentControllerDependency(
    NonMonitorableDependencyProvider[DeploymentControllerInput, DeploymentController],
):
    """Provides DeploymentController lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "deployment-controller"

    @asynccontextmanager
    async def provide(
        self, setup_input: DeploymentControllerInput
    ) -> AsyncIterator[DeploymentController]:
        """Initialize and provide a deployment controller.

        Args:
            setup_input: Input containing controllers, repositories, and config

        Yields:
            Initialized DeploymentController
        """
        controller = DeploymentController(
            DeploymentControllerArgs(
                scheduling_controller=setup_input.scheduling_controller,
                deployment_repository=setup_input.deployment_repository,
                config_provider=setup_input.config_provider,
                storage_manager=setup_input.storage_manager,
                event_producer=setup_input.event_producer,
                valkey_schedule=setup_input.valkey_schedule,
                revision_generator_registry=setup_input.revision_generator_registry,
            )
        )
        yield controller
