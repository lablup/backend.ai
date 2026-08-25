"""Component test fixtures for resource allocation v2 REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    Concern,
    ConcernMeta,
    GroupMeta,
)
from ai.backend.manager.api.adapters.resource_allocation.adapter import ResourceAllocationAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_allocation.handler import (
    V2ResourceAllocationHandler,
)
from ai.backend.manager.api.rest.v2.resource_allocation.registry import (
    register_v2_resource_allocation_routes,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.resource_allocation.repository import (
    ResourceAllocationRepository,
)
from ai.backend.manager.repositories.resource_preset.repository import (
    ResourcePresetRepository,
)
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.session.resource_allocation.service import (
    ResourceAllocationService,
)
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService


@pytest.fixture()
def resource_allocation_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    processor_registry: ProcessorRegistry[Any],
) -> ResourceAllocationProcessors:
    """Build real resource allocation processors with real DB and config."""
    ra_repo = ResourceAllocationRepository(
        db=database_engine,
        config_provider=config_provider,
    )
    rp_repo = ResourcePresetRepository(
        db=database_engine,
        valkey_stat=valkey_clients.stat,
        config_provider=config_provider,
    )
    service = ResourceAllocationService(
        resource_allocation_repository=ra_repo,
        resource_preset_repository=rp_repo,
    )
    groups = processor_registry.concern(ConcernMeta(Concern.RESOURCE_GROUP))
    return ResourceAllocationProcessors(
        groups.group(GroupMeta(USER_ENTITY_TYPE)),
        groups.group(GroupMeta(PROJECT_ENTITY_TYPE)),
        groups.group(GroupMeta(DOMAIN_ENTITY_TYPE)),
        groups.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)),
        groups.group(GroupMeta(SESSION_ENTITY_TYPE)),
        groups.group(GroupMeta(RESOURCE_PRESET_ENTITY_TYPE)),
        service,
    )


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> UserProcessors:
    """The adapter resolves an access key to its owner; the rest of the service is unused."""
    service = UserService(
        storage_manager=AsyncMock(),
        valkey_stat_client=AsyncMock(),
        agent_registry=AsyncMock(),
        user_repository=UserRepository(
            database_engine,
            V2DBOpsProvider(database_engine),
            KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
        ),
        secret_repository=AsyncMock(),
        scheduling_controller=AsyncMock(),
    )
    return UserProcessors(processor_registry.group(GroupMeta(USER_ENTITY_TYPE)), service)


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
    resource_allocation_processors: ResourceAllocationProcessors,
    domain_processors: DomainProcessors,
    user_processors: UserProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Register v2 resource allocation REST routes for testing."""
    processors = MagicMock(spec=Processors)
    # spec= reads dir(), which omits value-less annotations, so build the branch itself.
    processors.session = MagicMock(spec=SessionProcessors)
    processors.domain = domain_processors
    processors.user = user_processors
    processors.session.resource_allocation = resource_allocation_processors

    adapter = ResourceAllocationAdapter(
        processors=processors,
        config_provider=config_provider,
    )
    handler = V2ResourceAllocationHandler(adapter=adapter)

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_allocation_routes(handler, route_deps))
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


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with regular user keypair for v2 REST endpoints."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
