from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.rbac.request import (
    CreateRoleRequest,
    PurgeRoleRequest,
)
from ai.backend.common.dto.manager.rbac.response import CreateRoleResponse
from ai.backend.common.dto.manager.rbac.types import RoleSource, RoleStatus
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService

RoleFactory = Callable[..., Coroutine[Any, Any, CreateRoleResponse]]


@pytest.fixture()
def permission_controller_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerProcessors:
    repo = PermissionControllerRepository(database_engine)
    service = PermissionControllerService(repo)
    return PermissionControllerProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for RBAC-domain tests."""
    rbac_registry = register_rbac_routes(
        RBACHandler(permission_controller=permission_controller_processors), route_deps
    )
    return [
        register_admin_routes(
            AdminHandler(
                gql_schema=MagicMock(), gql_deps=MagicMock(), strawberry_schema=MagicMock()
            ),
            route_deps,
            sub_registries=[rbac_registry],
        ),
    ]


@pytest.fixture()
async def role_factory(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[RoleFactory]:
    """Factory fixture that creates roles via SDK and purges them on teardown."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateRoleResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-role-{unique}",
            "source": RoleSource.CUSTOM,
            "status": RoleStatus.ACTIVE,
            "description": f"Test role {unique}",
        }
        params.update(overrides)
        result = await admin_registry.rbac.create_role(CreateRoleRequest(**params))
        created_ids.append(result.role.id)
        return result

    yield _create

    for role_id in reversed(created_ids):
        try:
            await admin_registry.rbac.purge_role(PurgeRoleRequest(role_id=role_id))
        except Exception:
            pass


@pytest.fixture()
async def target_role(
    role_factory: RoleFactory,
) -> CreateRoleResponse:
    """Pre-created role for tests that need an existing role."""
    return await role_factory()
