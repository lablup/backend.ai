from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import scaling_group as _scaling_group_api
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

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_SCALING_GROUP_SERVER_SUBAPP_MODULES = (_auth_api, _scaling_group_api)


@asynccontextmanager
async def _scaling_group_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for scaling-group-domain component tests.

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
    # _TestConfigProvider skips super().__init__() so _legacy_etcd_config_loader
    # is never set.  The @server_status_required decorator (used by both
    # scaling-group handlers) calls
    # config_provider.legacy_etcd_config_loader.get_manager_status() which is
    # async.  Inject a MagicMock with an AsyncMock method so the check passes.
    mock_legacy_loader = MagicMock()
    mock_legacy_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    root_ctx.config_provider._legacy_etcd_config_loader = mock_legacy_loader

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
def server_subapp_pkgs() -> list[str]:
    """Load only the subapps required for scaling-group-domain tests."""
    return [".auth", ".scaling_group"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for scaling-group-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _scaling_group_domain_ctx: repositories and processors wired with real clients
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
        _scaling_group_domain_ctx,
    ]
