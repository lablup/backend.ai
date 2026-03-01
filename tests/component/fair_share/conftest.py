from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import fair_share as _fair_share_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.fair_share.registry import register_fair_share_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.scaling_group import sgroups_for_groups
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

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_FAIR_SHARE_SERVER_SUBAPP_MODULES = (_auth_api, _fair_share_api)


@asynccontextmanager
async def _fair_share_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for fair-share-domain component tests.

    Relies on the preceding cleanup contexts having already initialized:
    - redis_ctx      → root_ctx.valkey_* (all 8 clients)
    - database_ctx   → root_ctx.db
    - monitoring_ctx → root_ctx.error_monitor / stats_monitor
    - storage_manager_ctx  → root_ctx.storage_manager
    - message_queue_ctx    → root_ctx.message_queue
    - event_producer_ctx   → root_ctx.event_producer / event_fetcher
    - event_hub_ctx        → root_ctx.event_hub
    - background_task_ctx  → root_ctx.background_task_manager

    Only agent_registry is left as MagicMock because it requires live gRPC
    connections to real agents, which are not available in component tests.
    """
    _mock_loader = MagicMock()
    _mock_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    root_ctx.config_provider._legacy_etcd_config_loader = _mock_loader
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
                # agent_registry requires gRPC connections to real agents — not feasible
                # in the component test environment; kept as MagicMock.
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
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for fair-share-domain tests."""
    return [register_auth_routes, register_fair_share_routes]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for fair-share-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _fair_share_domain_ctx: repositories and processors wired with real clients
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
        _fair_share_domain_ctx,
    ]


@pytest.fixture()
async def group_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    scaling_group_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test group with scaling-group association for fair-share tests."""
    group_id = uuid.uuid4()
    group_name = f"group-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Test group {group_name}",
                is_active=True,
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        await conn.execute(
            sa.insert(sgroups_for_groups).values(
                scaling_group=scaling_group_fixture,
                group=group_id,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(
            sgroups_for_groups.delete().where(sgroups_for_groups.c.group == group_id)
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))
