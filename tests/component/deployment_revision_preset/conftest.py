"""Component test fixtures for deployment revision preset v2 CRUD."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

from ai.backend.manager.api.adapters.deployment_revision_preset import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.deployment_revision_preset.handler import (
    V2DeploymentRevisionPresetHandler,
)
from ai.backend.manager.api.rest.v2.deployment_revision_preset.registry import (
    register_v2_deployment_revision_preset_routes,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.services.deployment_revision_preset.processors import (
    DeploymentRevisionPresetProcessors,
)
from ai.backend.manager.services.deployment_revision_preset.service import (
    DeploymentRevisionPresetService,
)
from ai.backend.manager.services.processors import Processors


@pytest.fixture()
def deployment_revision_preset_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> DeploymentRevisionPresetProcessors:
    repo = DeploymentRevisionPresetRepository(database_engine)
    service = DeploymentRevisionPresetService(repo)
    return DeploymentRevisionPresetProcessors(
        service=service,
        action_monitors=[],
        validators=MagicMock(),
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    deployment_revision_preset_processors: DeploymentRevisionPresetProcessors,
) -> list[RouteRegistry]:
    processors = MagicMock(spec=Processors)
    processors.deployment_revision_preset = deployment_revision_preset_processors
    adapter = DeploymentRevisionPresetAdapter(processors)
    handler = V2DeploymentRevisionPresetHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_deployment_revision_preset_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
