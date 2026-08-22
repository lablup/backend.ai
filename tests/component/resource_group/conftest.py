"""Component test fixtures for resource group allow/disallow v2 REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_group.handler import V2ResourceGroupHandler
from ai.backend.manager.api.rest.v2.resource_group.registry import (
    register_v2_resource_group_routes,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService


@pytest.fixture()
def resource_group_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> ResourceGroupProcessors:
    repo = ResourceGroupRepository(database_engine)
    service = ResourceGroupService(repo)
    return ResourceGroupProcessors(
        processor_registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), service
    )


@pytest.fixture()
def domain_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> DomainProcessors:
    """The adapter resolves a domain name to its id, so this runs against the DB."""
    service = DomainService(
        repository=DomainRepository(database_engine, V2DBOpsProvider(database_engine))
    )
    return DomainProcessors(processor_registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)), service, [])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    resource_group_processors: ResourceGroupProcessors,
    domain_processors: DomainProcessors,
) -> list[RouteRegistry]:
    """Register v2 resource group REST routes for testing."""
    processors = MagicMock(spec=Processors)
    processors.resource_group = resource_group_processors
    processors.domain = domain_processors

    adapter = ResourceGroupAdapter(
        processors,
        deployment_coordinator=MagicMock(),
        schedule_coordinator=MagicMock(),
    )
    handler = V2ResourceGroupHandler(adapter=adapter)

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_group_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair for v2 REST endpoints."""
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
