from __future__ import annotations

import secrets
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

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

# Statically imported so that Pants includes these modules in the test PEX.
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import resource_policy as _resource_policy_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    event_hub_ctx,
    event_producer_ctx,
    message_queue_ctx,
    monitoring_ctx,
    redis_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs

_RESOURCE_POLICY_SERVER_SUBAPP_MODULES = (_auth_api, _resource_policy_api)

KeypairPolicyFactory = Callable[..., Coroutine[Any, Any, CreateKeypairResourcePolicyResponse]]
UserPolicyFactory = Callable[..., Coroutine[Any, Any, CreateUserResourcePolicyResponse]]
ProjectPolicyFactory = Callable[..., Coroutine[Any, Any, CreateProjectResourcePolicyResponse]]


@asynccontextmanager
async def _resource_policy_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for resource-policy component tests."""
    root_ctx.repositories = Repositories.create(
        RepositoryArgs(
            db=root_ctx.db,
            storage_manager=root_ctx.storage_manager,
            config_provider=root_ctx.config_provider,
            valkey_stat_client=root_ctx.valkey_stat,
            valkey_schedule_client=root_ctx.valkey_schedule,
            valkey_image_client=root_ctx.valkey_image,
            valkey_live_client=root_ctx.valkey_live,
        )
    )
    root_ctx.processors = Processors.create(
        ProcessorArgs(
            service_args=ServiceArgs(
                db=root_ctx.db,
                repositories=root_ctx.repositories,
                etcd=root_ctx.etcd,
                config_provider=root_ctx.config_provider,
                storage_manager=root_ctx.storage_manager,
                valkey_stat_client=root_ctx.valkey_stat,
                valkey_live=root_ctx.valkey_live,
                valkey_artifact_client=root_ctx.valkey_artifact,
                error_monitor=root_ctx.error_monitor,
                event_fetcher=root_ctx.event_fetcher,
                background_task_manager=root_ctx.background_task_manager,
                event_hub=root_ctx.event_hub,
                event_producer=root_ctx.event_producer,
                agent_registry=MagicMock(),
                idle_checker_host=MagicMock(),
                event_dispatcher=MagicMock(),
                hook_plugin_ctx=MagicMock(),
                scheduling_controller=MagicMock(),
                deployment_controller=MagicMock(),
                revision_generator_registry=MagicMock(),
                agent_cache=MagicMock(),
                notification_center=MagicMock(),
                appproxy_client_pool=MagicMock(),
                prometheus_client=MagicMock(),
            ),
        ),
        [],
    )
    yield


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    return [".auth", ".resource_policy"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _resource_policy_domain_ctx,
    ]


@pytest.fixture()
async def keypair_policy_factory(
    admin_registry: BackendAIClientRegistry,
) -> AsyncIterator[KeypairPolicyFactory]:
    """Factory fixture that creates keypair resource policies via SDK and deletes them on teardown."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateKeypairResourcePolicyResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-kp-policy-{unique}",
        }
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
        params: dict[str, Any] = {
            "name": f"test-user-policy-{unique}",
        }
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
        params: dict[str, Any] = {
            "name": f"test-proj-policy-{unique}",
        }
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


@pytest.fixture()
async def target_keypair_policy(
    keypair_policy_factory: KeypairPolicyFactory,
) -> CreateKeypairResourcePolicyResponse:
    return await keypair_policy_factory()


@pytest.fixture()
async def target_user_policy(
    user_policy_factory: UserPolicyFactory,
) -> CreateUserResourcePolicyResponse:
    return await user_policy_factory()


@pytest.fixture()
async def target_project_policy(
    project_policy_factory: ProjectPolicyFactory,
) -> CreateProjectResourcePolicyResponse:
    return await project_policy_factory()
