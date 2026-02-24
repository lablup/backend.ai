from __future__ import annotations

import secrets
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.resource_policy.request import (
    CreateKeypairResourcePolicyRequest,
    CreateProjectResourcePolicyRequest,
    CreateUserResourcePolicyRequest,
    DeleteKeypairResourcePolicyRequest,
    DeleteProjectResourcePolicyRequest,
    DeleteUserResourcePolicyRequest,
)
from ai.backend.common.dto.manager.resource_policy.response import (
    CreateKeypairResourcePolicyResponse,
    CreateProjectResourcePolicyResponse,
    CreateUserResourcePolicyResponse,
)

KeypairPolicyFactory = Callable[..., Coroutine[Any, Any, CreateKeypairResourcePolicyResponse]]
UserPolicyFactory = Callable[..., Coroutine[Any, Any, CreateUserResourcePolicyResponse]]
ProjectPolicyFactory = Callable[..., Coroutine[Any, Any, CreateProjectResourcePolicyResponse]]


@pytest.fixture()
async def keypair_policy_factory(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[KeypairPolicyFactory]:
    """Factory fixture that creates keypair resource policies via SDK and deletes them on teardown."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateKeypairResourcePolicyResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {"name": f"test-kp-integ-{unique}"}
        params.update(overrides)
        result = await admin_registry.resource_policy.create_keypair_policy(
            CreateKeypairResourcePolicyRequest(**params)
        )
        created_names.append(result.item.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_registry.resource_policy.delete_keypair_policy(
                DeleteKeypairResourcePolicyRequest(name=name)
            )
        except Exception:
            pass


@pytest.fixture()
async def user_policy_factory(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[UserPolicyFactory]:
    """Factory fixture that creates user resource policies via SDK and deletes them on teardown."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateUserResourcePolicyResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {"name": f"test-user-integ-{unique}"}
        params.update(overrides)
        result = await admin_registry.resource_policy.create_user_policy(
            CreateUserResourcePolicyRequest(**params)
        )
        created_names.append(result.item.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_registry.resource_policy.delete_user_policy(
                DeleteUserResourcePolicyRequest(name=name)
            )
        except Exception:
            pass


@pytest.fixture()
async def project_policy_factory(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[ProjectPolicyFactory]:
    """Factory fixture that creates project resource policies via SDK and deletes them on teardown."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateProjectResourcePolicyResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {"name": f"test-proj-integ-{unique}"}
        params.update(overrides)
        result = await admin_registry.resource_policy.create_project_policy(
            CreateProjectResourcePolicyRequest(**params)
        )
        created_names.append(result.item.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_registry.resource_policy.delete_project_policy(
                DeleteProjectResourcePolicyRequest(name=name)
            )
        except Exception:
            pass
