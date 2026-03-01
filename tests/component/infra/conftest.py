from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot, SlotName, SlotTypes, current_resource_slots

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import etcd as _etcd_api
from ai.backend.manager.api import resource as _resource_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.etcd.registry import register_etcd_routes
from ai.backend.manager.api.rest.resource.registry import register_resource_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
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

_INFRA_SERVER_SUBAPP_MODULES = (_auth_api, _etcd_api, _resource_api)


def _make_mock_agent_registry() -> MagicMock:
    """Create a MagicMock agent_registry with awaitable async stubs."""
    mock = MagicMock()
    mock.recalc_resource_usage = AsyncMock(return_value=None)
    return mock


@asynccontextmanager
async def _infra_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for infra-domain component tests.

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
    # is never set.  The @server_status_required decorator calls
    # config_provider.legacy_etcd_config_loader.get_manager_status() which is
    # async.  Inject a MagicMock with an AsyncMock method so the check passes.
    mock_legacy_loader = MagicMock()
    mock_legacy_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    # Read-only etcd endpoints call these methods on legacy_etcd_config_loader;
    # return minimal valid data so the endpoints respond successfully.
    mock_legacy_loader.get_resource_slots = AsyncMock(return_value={"cpu": "count", "mem": "bytes"})
    mock_legacy_loader.get_vfolder_types = AsyncMock(return_value=["user", "group"])
    mock_legacy_loader.register_myself = AsyncMock(return_value=None)
    mock_legacy_loader.deregister_myself = AsyncMock(return_value=None)
    # check_presets reads group_resource_visibility via get_raw(); return None
    # so the repository treats it as "no visibility restriction".
    mock_legacy_loader.get_raw = AsyncMock(return_value=None)
    root_ctx.config_provider._legacy_etcd_config_loader = mock_legacy_loader

    # ResourceSlot.normalize_slots() reads this ContextVar; set it so that
    # list_presets / check_presets do not raise LookupError.
    current_resource_slots.set({
        SlotName("cpu"): SlotTypes("count"),
        SlotName("mem"): SlotTypes("bytes"),
    })

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
                # in the component test environment; kept as MagicMock with async stubs
                # for methods that are awaited (e.g. recalculate_usage).
                agent_registry=_make_mock_agent_registry(),
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
    """Load only the modules required for infra-domain tests."""
    return [register_auth_routes, register_etcd_routes, register_resource_routes]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for infra-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _infra_domain_ctx: repositories and processors wired with real clients
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
        _infra_domain_ctx,
    ]


@pytest.fixture()
async def group_name_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
) -> str:
    """Query the group name from the database for the test group."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(GroupRow.__table__.c.name).where(GroupRow.__table__.c.id == group_fixture)
        )
        row = result.first()
        assert row is not None
        return str(row[0])


@pytest.fixture()
async def resource_preset_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[dict[str, str]]:
    """Insert a test resource preset and yield its metadata.

    Used for list_presets and check_presets tests. Cleaned up after each test.
    """
    preset_id = uuid.uuid4()
    preset_name = f"test-preset-{preset_id.hex[:8]}"
    resource_slots = ResourceSlot({"cpu": "1", "mem": "1073741824"})
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ResourcePresetRow.__table__).values(
                id=preset_id,
                name=preset_name,
                resource_slots=resource_slots,
                shared_memory=None,
                scaling_group_name=None,
            )
        )
    yield {"id": str(preset_id), "name": preset_name}
    async with db_engine.begin() as conn:
        await conn.execute(
            ResourcePresetRow.__table__.delete().where(
                ResourcePresetRow.__table__.c.id == preset_id
            )
        )
