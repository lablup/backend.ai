from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.user.types import UserRole

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.group import association_groups_users
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.user import users
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

_AUTH_SERVER_SUBAPP_MODULES = (_auth_api,)


@dataclass
class AuthUserFixtureData:
    """Extended user fixture that retains the raw password for auth tests."""

    user_uuid: uuid.UUID
    access_key: str
    secret_key: str
    password: str
    email: str
    domain_name: str


@asynccontextmanager
async def _auth_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for auth-domain component tests.

    Relies on the preceding cleanup contexts having already initialized:
    - redis_ctx      -> root_ctx.valkey_* (all 8 clients)
    - database_ctx   -> root_ctx.db
    - monitoring_ctx -> root_ctx.error_monitor / stats_monitor
    - storage_manager_ctx  -> root_ctx.storage_manager
    - message_queue_ctx    -> root_ctx.message_queue
    - event_producer_ctx   -> root_ctx.event_producer / event_fetcher
    - event_hub_ctx        -> root_ctx.event_hub
    - background_task_ctx  -> root_ctx.background_task_manager

    Only agent_registry is left as MagicMock because it requires live gRPC
    connections to real agents, which are not available in component tests.
    """
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
    """Load only the auth subapp for auth-domain tests."""
    return [".auth"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for auth-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _auth_domain_ctx: repositories and processors wired with real clients
    """
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _auth_domain_ctx,
    ]


@pytest.fixture()
async def auth_user_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    domain_fixture: str,
    resource_policy_fixture: str,
) -> AsyncIterator[AuthUserFixtureData]:
    """Insert a regular user with a known password for auth tests.

    Unlike the parent conftest's user fixtures, this one retains the raw
    password so that tests can call authorize, signout, and update_password.
    """
    unique_id = secrets.token_hex(4)
    email = f"auth-user-{unique_id}@test.local"
    password = f"TestP@ss{unique_id}"
    data = AuthUserFixtureData(
        user_uuid=uuid.uuid4(),
        access_key=f"AKTEST{secrets.token_hex(7).upper()}",
        secret_key=secrets.token_hex(20),
        password=password,
        email=email,
        domain_name=domain_fixture,
    )
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(users).values(
                uuid=str(data.user_uuid),
                username=f"auth-user-{unique_id}",
                email=email,
                password=PasswordInfo(
                    password=password,
                    algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                    rounds=600_000,
                    salt_size=32,
                ),
                need_password_change=False,
                full_name=f"Auth User {unique_id}",
                description=f"Test auth user {unique_id}",
                status=UserStatus.ACTIVE,
                status_info="admin-requested",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                role=UserRole.USER,
            )
        )
        await conn.execute(
            sa.insert(keypairs).values(
                user_id=email,
                access_key=data.access_key,
                secret_key=data.secret_key,
                is_active=True,
                resource_policy=resource_policy_fixture,
                rate_limit=30000,
                num_queries=0,
                is_admin=False,
                user=str(data.user_uuid),
            )
        )
        await conn.execute(
            sa.insert(association_groups_users).values(
                group_id=str(group_fixture),
                user_id=str(data.user_uuid),
            )
        )
    yield data
    async with db_engine.begin() as conn:
        await conn.execute(
            association_groups_users.delete().where(
                association_groups_users.c.user_id == str(data.user_uuid)
            )
        )
        await conn.execute(keypairs.delete().where(keypairs.c.access_key == data.access_key))
        await conn.execute(users.delete().where(users.c.uuid == str(data.user_uuid)))


@pytest.fixture()
async def auth_user_registry(
    server: Any,
    auth_user_fixture: AuthUserFixtureData,
) -> AsyncIterator[BackendAIClientRegistry]:
    """Create a BackendAIClientRegistry authenticated as the auth user."""
    registry = await BackendAIClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=auth_user_fixture.access_key,
            secret_key=auth_user_fixture.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()
