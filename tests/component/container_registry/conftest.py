from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.container_registry.handler import ContainerRegistryHandler
from ai.backend.manager.api.rest.container_registry.registry import (
    register_container_registry_routes,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryProcessors:
    repo = ContainerRegistryRepository(database_engine)
    service = ContainerRegistryService(database_engine, repo)
    return ContainerRegistryProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    container_registry_processors: ContainerRegistryProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for container-registry-domain tests."""
    return [
        register_container_registry_routes(
            ContainerRegistryHandler(container_registry=container_registry_processors),
            route_deps,
        ),
    ]


@pytest.fixture()
async def container_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID.

    Used for patch endpoint tests. Cleaned up after each test.
    """
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.test.local",
                registry_name=f"test-registry-{registry_id.hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
async def harbor_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test HARBOR2 container registry and yield its UUID.

    Used for harbor webhook endpoint tests. Cleaned up after each test.
    """
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://harbor.test.local",
                registry_name=f"harbor-test-{registry_id.hex[:8]}",
                type=ContainerRegistryType.HARBOR2,
                project="testproject",
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
async def registry_factory(
    db_engine: SAEngine,
) -> AsyncIterator[Callable[..., Any]]:
    """Factory that inserts test container registries and tracks them for cleanup.

    Yields a callable that accepts keyword arguments matching ContainerRegistryRow columns.
    Required fields: url, registry_name, type.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**kwargs: Any) -> dict[str, Any]:
        registry_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": registry_id,
            "url": "https://registry.test.local",
            "registry_name": f"test-{registry_id.hex[:8]}",
            "type": ContainerRegistryType.DOCKER,
        }
        defaults.update(kwargs)
        if "id" not in kwargs:
            defaults["id"] = registry_id
            registry_id_to_track = registry_id
        else:
            registry_id_to_track = defaults["id"]
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(ContainerRegistryRow.__table__).values(**defaults))
        created_ids.append(registry_id_to_track)
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for rid in created_ids:
            await conn.execute(
                ContainerRegistryRow.__table__.delete().where(
                    ContainerRegistryRow.__table__.c.id == rid
                )
            )
