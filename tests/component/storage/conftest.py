from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.object_storage.handler import ObjectStorageHandler
from ai.backend.manager.api.rest.object_storage.registry import register_object_storage_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.vfs_storage.handler import VFSStorageHandler
from ai.backend.manager.api.rest.vfs_storage.registry import register_vfs_storage_routes
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.artifact.repository import ArtifactRepository
from ai.backend.manager.repositories.object_storage.repository import ObjectStorageRepository
from ai.backend.manager.repositories.storage_namespace.repository import StorageNamespaceRepository
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.object_storage.processors import ObjectStorageProcessors
from ai.backend.manager.services.object_storage.service import ObjectStorageService
from ai.backend.manager.services.storage_namespace.processors import StorageNamespaceProcessors
from ai.backend.manager.services.storage_namespace.service import StorageNamespaceService
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors
from ai.backend.manager.services.vfs_storage.service import VFSStorageService

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_STORAGE_SERVER_SUBAPP_MODULES = (_auth_api,)


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
    object_storage_processors: ObjectStorageProcessors,
    storage_namespace_processors: StorageNamespaceProcessors,
    vfs_storage_processors: VFSStorageProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for storage-domain tests."""
    return [
        register_object_storage_routes(
            ObjectStorageHandler(
                object_storage=object_storage_processors,
                storage_namespace=storage_namespace_processors,
            ),
            route_deps,
        ),
        register_vfs_storage_routes(
            VFSStorageHandler(vfs_storage=vfs_storage_processors), route_deps
        ),
    ]
