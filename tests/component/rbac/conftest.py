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
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps

RoleFactory = Callable[..., Coroutine[Any, Any, CreateRoleResponse]]


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for RBAC-domain tests."""
    mock_processors = MagicMock()
    return [
        register_auth_routes(AuthHandler(auth=mock_processors.auth), route_deps),
        register_admin_routes(
            AdminHandler(gql_schema=MagicMock(), gql_deps=MagicMock()),
            route_deps,
            sub_registries=[],
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
