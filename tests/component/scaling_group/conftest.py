from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.rest.resource_group.handler import ResourceGroupHandler
from ai.backend.manager.api.rest.resource_group.registry import register_resource_group_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.project.repositories import ProjectRepositories
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService


@pytest.fixture()
def resource_group_processors(
    database_engine: ExtendedAsyncSAEngine, processor_registry: ProcessorRegistry[Any]
) -> ResourceGroupProcessors:
    repo = ResourceGroupRepository(database_engine, V2DBOpsProvider(database_engine))
    service = ResourceGroupService(repo)
    return ResourceGroupProcessors(
        processor_registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), service
    )


@pytest.fixture()
def domain_processors(
    database_engine: ExtendedAsyncSAEngine, processor_registry: ProcessorRegistry[Any]
) -> DomainProcessors:
    """The handler resolves the caller's domain name to its id, so this runs against the DB."""
    service = DomainService(
        repository=DomainRepository(database_engine, V2DBOpsProvider(database_engine))
    )
    return DomainProcessors(processor_registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)), service, [])


@pytest.fixture()
def project_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    storage_manager: AsyncMock,
    processor_registry: ProcessorRegistry[Any],
) -> ProjectProcessors:
    """The handler resolves a group name to its project id, so this runs against the DB."""
    repositories = ProjectRepositories(
        repository=ProjectRepository(
            database_engine,
            V2DBOpsProvider(database_engine),
            config_provider,
            valkey_clients.stat,
            storage_manager,
        )
    )
    service = ProjectService(storage_manager, config_provider, valkey_clients.stat, repositories)
    return ProjectProcessors(processor_registry.group(GroupMeta(PROJECT_ENTITY_TYPE)), service)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    resource_group_processors: ResourceGroupProcessors,
    domain_processors: DomainProcessors,
    project_processors: ProjectProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for resource-group tests."""
    return [
        register_resource_group_routes(
            ResourceGroupHandler(
                resource_group=resource_group_processors,
                domain=domain_processors,
                project=project_processors,
            ),
            route_deps,
        ),
    ]
