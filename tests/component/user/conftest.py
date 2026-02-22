from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    PurgeUserRequest,
)

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import user as _user_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.utils import connect_database
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs

_USER_SERVER_SUBAPP_MODULES = (_user_api,)

UserFactory = Callable[..., Coroutine[Any, Any, CreateUserResponse]]


@asynccontextmanager
async def _user_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up db, repositories and processors for user-domain component tests.

    Uses a real database engine and all user-related repositories.
    All other dependencies (valkey, storage, agents, etc.) are replaced
    with MagicMock to avoid starting unrelated production services.
    """
    async with connect_database(root_ctx.config_provider.config.db) as db:
        root_ctx.db = db
        root_ctx.repositories = Repositories.create(
            RepositoryArgs(
                db=db,
                storage_manager=MagicMock(),
                config_provider=root_ctx.config_provider,
                valkey_stat_client=MagicMock(),
                valkey_schedule_client=MagicMock(),
                valkey_image_client=MagicMock(),
                valkey_live_client=MagicMock(),
            )
        )
        root_ctx.processors = Processors.create(
            ProcessorArgs(
                service_args=ServiceArgs(
                    db=db,
                    repositories=root_ctx.repositories,
                    etcd=root_ctx.etcd,
                    config_provider=root_ctx.config_provider,
                    storage_manager=MagicMock(),
                    valkey_stat_client=MagicMock(),
                    valkey_live=MagicMock(),
                    valkey_artifact_client=MagicMock(),
                    event_fetcher=MagicMock(),
                    background_task_manager=MagicMock(),
                    event_hub=MagicMock(),
                    agent_registry=MagicMock(),
                    error_monitor=MagicMock(),
                    idle_checker_host=MagicMock(),
                    event_dispatcher=MagicMock(),
                    hook_plugin_ctx=MagicMock(),
                    scheduling_controller=MagicMock(),
                    deployment_controller=MagicMock(),
                    revision_generator_registry=MagicMock(),
                    event_producer=MagicMock(),
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
    """Load only the subapps required for user-domain tests."""
    return [".user"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide the single cleanup context for user-domain component tests."""
    return [_user_domain_ctx]


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
