from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    PurgeUserRequest,
    UserStatus,
)
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users

UserFactory = Callable[..., Coroutine[Any, Any, CreateUserResponse]]


@pytest.fixture()
def server_module_registries(route_deps: RouteDeps) -> list[RouteRegistry]:
    """Load only the modules required for user-domain tests."""
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
async def user_factory(
    admin_registry: BackendAIClientRegistry,
    domain_fixture: str,
    resource_policy_fixture: str,
    db_engine: SAEngine,
) -> AsyncIterator[UserFactory]:
    """Factory fixture that creates users via SDK and purges them on teardown."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateUserResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "email": f"test-{unique}@test.local",
            "username": f"test-{unique}",
            "password": "test-password-1234",
            "domain_name": domain_fixture,
            "resource_policy": resource_policy_fixture,
            "status": UserStatus.ACTIVE,
        }
        params.update(overrides)
        result = await admin_registry.user.create(CreateUserRequest(**params))
        created_ids.append(result.user.id)
        return result

    yield _create

    for uid in reversed(created_ids):
        try:
            await admin_registry.user.purge(PurgeUserRequest(user_id=uid))
        except Exception:
            # Fallback: remove user rows directly when the API purge cannot complete.
            # This handles cases where the server is unreachable during teardown.
            async with db_engine.begin() as conn:
                await conn.execute(
                    association_groups_users.delete().where(
                        association_groups_users.c.user_id == str(uid)
                    )
                )
                await conn.execute(keypairs.delete().where(keypairs.c.user == str(uid)))
                await conn.execute(users.delete().where(users.c.uuid == str(uid)))


@pytest.fixture()
async def target_user(
    user_factory: UserFactory,
) -> CreateUserResponse:
    """Pre-created user for tests that need an existing user."""
    return await user_factory()
