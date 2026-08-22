from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.rest.resource_group.handler import ResourceGroupHandler
from ai.backend.manager.api.rest.resource_group.registry import register_resource_group_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService


@pytest.fixture()
def resource_group_processors(
    database_engine: ExtendedAsyncSAEngine, processor_registry: ProcessorRegistry[Any]
) -> ResourceGroupProcessors:
    repo = ResourceGroupRepository(database_engine)
    service = ResourceGroupService(repo)
    return ResourceGroupProcessors(
        processor_registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), service
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    resource_group_processors: ResourceGroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for resource-group tests."""
    return [
        register_resource_group_routes(
            ResourceGroupHandler(resource_group=resource_group_processors), route_deps
        ),
    ]
