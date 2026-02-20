from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    PurgeUserRequest,
)

UserFactory = Callable[..., Coroutine[Any, Any, CreateUserResponse]]


@pytest.fixture()
async def user_factory(
    admin_registry: BackendAIClientRegistry,
    domain_fixture: str,
    resource_policy_fixture: str,
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
            pass


@pytest.fixture()
async def target_user(
    user_factory: UserFactory,
) -> CreateUserResponse:
    """Pre-created user for tests that need an existing user."""
    return await user_factory()
