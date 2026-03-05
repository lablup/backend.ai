from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.service.handler import ServiceHandler
from ai.backend.manager.api.rest.service.registry import register_service_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
    RevisionGeneratorRegistryArgs,
)


@pytest.fixture()
def model_serving_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    background_task_manager: BackgroundTaskManager,
) -> ModelServingProcessors:
    """Real ModelServingProcessors with real service and repository."""
    ms_repo = ModelServingRepository(database_engine)
    deployment_repo = DeploymentRepository(
        database_engine,
        storage_manager,
        valkey_clients.stat,
        valkey_clients.live,
        valkey_clients.schedule,
    )
    revision_gen = RevisionGeneratorRegistry(
        RevisionGeneratorRegistryArgs(deployment_repository=deployment_repo)
    )
    service = ModelServingService(
        agent_registry=AsyncMock(),
        background_task_manager=background_task_manager,
        event_dispatcher=AsyncMock(),
        event_hub=EventHub(),
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_live=valkey_clients.live,
        repository=ms_repo,
        deployment_repository=deployment_repo,
        deployment_controller=AsyncMock(),
        scheduling_controller=AsyncMock(),
        revision_generator_registry=revision_gen,
    )
    return ModelServingProcessors(service=service, action_monitors=[])


@pytest.fixture()
def auto_scaling_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ModelServingAutoScalingProcessors:
    """Real ModelServingAutoScalingProcessors with real AutoScalingService."""
    repo = ModelServingRepository(database_engine)
    service = AutoScalingService(repository=repo)
    return ModelServingAutoScalingProcessors(service=service, action_monitors=[])


@pytest.fixture()
def deployment_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
    valkey_clients: ValkeyClients,
) -> DeploymentProcessors:
    """Real DeploymentProcessors with real DeploymentService and DeploymentRepository."""
    repo = DeploymentRepository(
        database_engine,
        storage_manager,
        valkey_clients.stat,
        valkey_clients.live,
        valkey_clients.schedule,
    )
    deployment_controller = AsyncMock()
    service = DeploymentService(deployment_controller, repo)
    return DeploymentProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    deployment_processors: DeploymentProcessors,
    model_serving_processors: ModelServingProcessors,
    auto_scaling_processors: ModelServingAutoScalingProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for model-serving tests."""
    return [
        register_service_routes(
            ServiceHandler(
                auth=auth_processors,
                deployment=deployment_processors,
                model_serving=model_serving_processors,
                model_serving_auto_scaling=auto_scaling_processors,
            ),
            route_deps,
        ),
    ]
