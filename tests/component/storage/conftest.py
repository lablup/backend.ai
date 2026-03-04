from __future__ import annotations

import pytest

from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.object_storage.registry import register_object_storage_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.api.rest.vfs_storage.registry import register_vfs_storage_routes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_STORAGE_SERVER_SUBAPP_MODULES = (_auth_api,)


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for storage-domain tests."""
    return [register_auth_routes, register_object_storage_routes, register_vfs_storage_routes]
