from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.quota_scope.handler import QuotaScopeHandler
from ai.backend.manager.api.rest.quota_scope.registry import register_quota_scope_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors
from ai.backend.manager.services.vfs_storage.service import VFSStorageService


@pytest.fixture()
def vfs_storage_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: AsyncMock,
) -> VFSStorageProcessors:
    repo = VFSStorageRepository(database_engine)
    service = VFSStorageService(repo, storage_manager=storage_manager)
    return VFSStorageProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    vfs_storage_processors: VFSStorageProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for quota-scope-domain tests."""
    quota_scope_registry = register_quota_scope_routes(
        QuotaScopeHandler(vfs_storage=vfs_storage_processors), route_deps
    )
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(), gql_deps=MagicMock(), strawberry_schema=MagicMock()
            ),
            route_deps,
            sub_registries=[quota_scope_registry],
        ),
    ]
