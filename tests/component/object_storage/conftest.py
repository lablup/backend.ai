from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.object_storage.handler import ObjectStorageHandler
from ai.backend.manager.api.rest.object_storage.registry import register_object_storage_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.object_storage.service import ObjectStorageService
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_OBJECT_STORAGE_SERVER_SUBAPP_MODULES = (_auth_api,)

ObjectStorageFixtureData = dict[str, Any]
ObjectStorageFactory = Callable[..., Coroutine[Any, Any, ObjectStorageFixtureData]]
StorageNamespaceFixtureData = dict[str, Any]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, StorageNamespaceFixtureData]]


@pytest.fixture()
def object_storage_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
    config_provider: ManagerConfigProvider,
) -> ObjectStorageProcessors:
    artifact_repository = ArtifactRepository(database_engine)
    object_storage_repository = ObjectStorageRepository(database_engine)
    storage_namespace_repository = StorageNamespaceRepository(database_engine)
    service = ObjectStorageService(
        artifact_repository=artifact_repository,
        object_storage_repository=object_storage_repository,
        storage_namespace_repository=storage_namespace_repository,
        storage_manager=storage_manager,
        config_provider=config_provider,
    )
    return ObjectStorageProcessors(service=service, action_monitors=[])


@pytest.fixture()
def storage_namespace_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> StorageNamespaceProcessors:
    storage_namespace_repository = StorageNamespaceRepository(database_engine)
    service = StorageNamespaceService(
        storage_namespace_repository=storage_namespace_repository,
    )
    return StorageNamespaceProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    object_storage_processors: ObjectStorageProcessors,
    storage_namespace_processors: StorageNamespaceProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for object-storage-domain tests."""
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
        register_object_storage_routes(
            ObjectStorageHandler(
                object_storage=object_storage_processors,
                storage_namespace=storage_namespace_processors,
            ),
            route_deps,
        ),
    ]


@pytest.fixture()
async def object_storage_factory(
    db_engine: SAEngine,
) -> AsyncIterator[ObjectStorageFactory]:
    """Factory that inserts ObjectStorageRow directly into DB.

    Yields a factory callable and cleans up all created rows on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> ObjectStorageFixtureData:
        unique = secrets.token_hex(4)
        storage_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": storage_id,
            "name": f"test-storage-{unique}",
            "host": "s3.example.com",
            "access_key": f"AK-{unique}",
            "secret_key": f"SK-{unique}",
            "endpoint": f"https://s3.example.com/{unique}",
            "region": "us-east-1",
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(ObjectStorageRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for sid in reversed(created_ids):
            await conn.execute(
                sa.delete(StorageNamespaceRow.__table__).where(
                    StorageNamespaceRow.__table__.c.storage_id == sid
                )
            )
            await conn.execute(
                sa.delete(ObjectStorageRow.__table__).where(ObjectStorageRow.__table__.c.id == sid)
            )


@pytest.fixture()
async def storage_namespace_factory(
    db_engine: SAEngine,
) -> AsyncIterator[StorageNamespaceFactory]:
    """Factory that inserts StorageNamespaceRow directly into DB.

    Yields a factory callable and cleans up all created rows on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> StorageNamespaceFixtureData:
        unique = secrets.token_hex(4)
        ns_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": ns_id,
            "namespace": f"test-bucket-{unique}",
        }
        defaults.update(overrides)
        if "storage_id" not in defaults:
            raise ValueError("storage_id is required for storage_namespace_factory")
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(StorageNamespaceRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for nid in reversed(created_ids):
            await conn.execute(
                sa.delete(StorageNamespaceRow.__table__).where(
                    StorageNamespaceRow.__table__.c.id == nid
                )
            )
