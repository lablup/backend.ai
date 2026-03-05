from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.object_storage.handler import ObjectStorageHandler
from ai.backend.manager.api.rest.object_storage.registry import register_object_storage_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.vfs_storage.handler import VFSStorageHandler
from ai.backend.manager.api.rest.vfs_storage.registry import register_vfs_storage_routes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_STORAGE_SERVER_SUBAPP_MODULES = (_auth_api,)


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for storage-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_object_storage_routes(
            ObjectStorageHandler(
                object_storage=mock_processors.object_storage,
                storage_namespace=mock_processors.storage_namespace,
            ),
            route_deps,
        ),
        register_vfs_storage_routes(
            VFSStorageHandler(vfs_storage=mock_processors.vfs_storage), route_deps
        ),
    ]
