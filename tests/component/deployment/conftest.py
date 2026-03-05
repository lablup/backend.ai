from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.deployment.handler import DeploymentAPIHandler
from ai.backend.manager.api.rest.deployment.registry import register_deployment_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService


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
    revision_generator_registry = MagicMock()
    service = DeploymentService(deployment_controller, repo, revision_generator_registry)
    return DeploymentProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    deployment_processors: DeploymentProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for deployment-domain tests."""
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
        register_deployment_routes(
            DeploymentAPIHandler(deployment=deployment_processors), route_deps
        ),
    ]
