from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.vfs_storage.handler import VFSStorageHandler
from ai.backend.manager.api.rest.vfs_storage.registry import register_vfs_storage_routes
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors
from ai.backend.manager.services.vfs_storage.service import VFSStorageService

# Statically imported so that Pants includes these modules in the test PEX.
_VFS_STORAGE_SERVER_SUBAPP_MODULES = (_auth_api,)

VFSStorageFixtureData = dict[str, Any]
VFSStorageFactory = Callable[..., Coroutine[Any, Any, VFSStorageFixtureData]]


@pytest.fixture()
def vfs_storage_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
) -> VFSStorageProcessors:
    vfs_storage_repository = VFSStorageRepository(database_engine)
    service = VFSStorageService(
        vfs_storage_repository=vfs_storage_repository,
        storage_manager=storage_manager,
    )
    return VFSStorageProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    vfs_storage_processors: VFSStorageProcessors,
) -> list[RouteRegistry]:
    """Load only the VFS storage routes for focused testing."""
    return [
        register_vfs_storage_routes(
            VFSStorageHandler(vfs_storage=vfs_storage_processors), route_deps
        ),
    ]


@pytest.fixture()
async def vfs_storage_factory(
    db_engine: SAEngine,
) -> AsyncIterator[VFSStorageFactory]:
    """Factory that inserts VFS storage rows directly into DB.

    Yields a factory callable and cleans up all created storages on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> VFSStorageFixtureData:
        storage_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": storage_id,
            "name": f"test-vfs-{storage_id.hex[:8]}",
            "host": "local:volume1",
            "base_path": "/mnt/vfs/test",
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(VFSStorageRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for sid in reversed(created_ids):
            await conn.execute(
                VFSStorageRow.__table__.delete().where(VFSStorageRow.__table__.c.id == sid)
            )


@pytest.fixture()
async def target_vfs_storage(
    vfs_storage_factory: VFSStorageFactory,
) -> VFSStorageFixtureData:
    """Pre-created VFS storage for tests that need an existing storage."""
    return await vfs_storage_factory()
