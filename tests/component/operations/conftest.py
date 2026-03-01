from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import logs as _logs_api
from ai.backend.manager.api import manager as _manager_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_module
from ai.backend.manager.api.rest.error_log.registry import register_error_log_module
from ai.backend.manager.api.rest.manager.registry import register_manager_api_module
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.agent import agents
from ai.backend.manager.models.error_logs import error_logs
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    distributed_lock_ctx,
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
_OPERATIONS_SERVER_SUBAPP_MODULES = (_auth_api, _logs_api, _manager_api)


async def _blocking_watch_manager_status() -> AsyncIterator[Any]:
    """Async generator that blocks indefinitely; cancelled on server shutdown."""
    try:
        while True:
            await asyncio.sleep(99999)
            yield  # makes this an async generator but never reached
    except (asyncio.CancelledError, GeneratorExit):
        return


@asynccontextmanager
async def _operations_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for operations-domain component tests.

    Also mocks lifecycle dependencies needed by logs and manager subapp init():
    - event_dispatcher: required by logs handler for GlobalTimer event consumption
    - legacy_etcd_config_loader: required by server_status_required decorator
      and manager handler's detect_status_update background task
    """
    _mock_loader = MagicMock()
    _mock_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    _mock_loader.update_manager_status = AsyncMock()
    _mock_loader.watch_manager_status = _blocking_watch_manager_status
    root_ctx.config_provider._legacy_etcd_config_loader = _mock_loader

    # Mock event_dispatcher (logs handler init calls event_dispatcher.consume())
    root_ctx.event_dispatcher = MagicMock()

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
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for operations-domain tests."""
    return [register_auth_module, register_error_log_module, register_manager_api_module]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for operations-domain component tests.

    Uses production contexts from server.py for real infrastructure plus
    distributed_lock_ctx (needed by logs handler GlobalTimer) and
    _operations_domain_ctx for repositories, processors, and lifecycle mocks.
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
        distributed_lock_ctx,
        _operations_domain_ctx,
    ]


@pytest.fixture()
async def agent_fixture(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[str]:
    """Insert a test agent record and yield its ID."""
    agent_id = f"i-test-agent-{secrets.token_hex(4)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(agents).values(
                id=agent_id,
                region="local",
                scaling_group=scaling_group_fixture,
                available_slots=ResourceSlot(),
                occupied_slots=ResourceSlot(),
                addr="127.0.0.1:6001",
                version="test",
                architecture="x86_64",
            )
        )
    yield agent_id


@pytest.fixture(autouse=True)
async def _cleanup_side_effects(
    db_engine: SAEngine,
    server: Any,
) -> AsyncIterator[None]:
    """Clean error_logs and agents tables after each test.

    Depends on ``server`` to ensure teardown runs before user/scaling-group
    fixture teardowns, which would otherwise hit FK violations.
    """
    yield
    async with db_engine.begin() as conn:
        await conn.execute(sa.delete(error_logs))
        await conn.execute(sa.delete(agents))
