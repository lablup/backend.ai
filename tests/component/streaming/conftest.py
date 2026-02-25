from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import stream as _stream_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow
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

_STREAMING_SERVER_SUBAPP_MODULES = (_auth_api, _stream_api)


@dataclass
class KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class UserFixtureData:
    user_uuid: uuid.UUID
    keypair: KeypairFixtureData


@dataclass
class SessionSeedData:
    session_id: SessionId
    session_name: str
    kernel_id: uuid.UUID
    access_key: str
    domain_name: str


@asynccontextmanager
async def _streaming_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for streaming component tests.

    Relies on the preceding cleanup contexts having already initialized:
    - redis_ctx      -> root_ctx.valkey_* (all 8 clients)
    - database_ctx   -> root_ctx.db
    - monitoring_ctx -> root_ctx.error_monitor / stats_monitor
    - storage_manager_ctx  -> root_ctx.storage_manager
    - message_queue_ctx    -> root_ctx.message_queue
    - event_producer_ctx   -> root_ctx.event_producer / event_fetcher
    - event_hub_ctx        -> root_ctx.event_hub
    - background_task_ctx  -> root_ctx.background_task_manager

    agent_registry, scheduling_controller, and other agent-dependent services
    are left as AsyncMock because they require live gRPC connections to real
    agents, which are not available in component tests.
    """
    # _TestConfigProvider skips super().__init__() so _legacy_etcd_config_loader
    # is never set.  The @server_status_required decorator (used by stream
    # handlers) calls config_provider._legacy_etcd_config_loader.get_manager_status()
    # which is async.  Inject a MagicMock with an AsyncMock method so the check passes.
    mock_legacy_loader = MagicMock()
    mock_legacy_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    root_ctx.config_provider._legacy_etcd_config_loader = mock_legacy_loader

    root_ctx.registry = AsyncMock()

    # stream_app_ctx() accesses root_ctx.event_dispatcher.subscribe() directly
    # (src/ai/backend/manager/api/stream.py:741), so we must set it on root_ctx.
    root_ctx.event_dispatcher = MagicMock()

    mock_idle_checker = AsyncMock()
    mock_idle_checker.get_idle_check_report = AsyncMock(return_value={})

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
                agent_registry=AsyncMock(),
                idle_checker_host=mock_idle_checker,
                event_dispatcher=AsyncMock(),
                hook_plugin_ctx=AsyncMock(),
                scheduling_controller=AsyncMock(),
                deployment_controller=AsyncMock(),
                revision_generator_registry=AsyncMock(),
                agent_cache=AsyncMock(),
                notification_center=AsyncMock(),
                appproxy_client_pool=AsyncMock(),
                prometheus_client=AsyncMock(),
            ),
        ),
        [],
    )
    yield


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """Load only the subapps required for streaming component tests."""
    return [".auth", ".stream"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for streaming component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _streaming_domain_ctx,
    ]


@pytest.fixture()
async def session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session + kernel with service_ports in the database.

    The kernel has ``service_ports`` populated so that
    ``get_stream_apps()`` returns a non-empty list.
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-stream-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_fixture,
                status=SessionStatus.RUNNING,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=kernel_id,
                session_id=session_id,
                session_creation_id=f"cid-{unique}",
                session_name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                cluster_mode="single-node",
                cluster_size=1,
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group=scaling_group_fixture,
                status=KernelStatus.RUNNING,
                status_info="",
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
                service_ports=[
                    {
                        "name": "jupyter",
                        "protocol": "http",
                        "container_ports": [8888],
                        "host_ports": [10001],
                    },
                    {
                        "name": "ttyd",
                        "protocol": "http",
                        "container_ports": [7681],
                        "host_ports": [10002],
                    },
                ],
            )
        )

    yield SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=kernel_id,
        access_key=admin_user_fixture.keypair.access_key,
        domain_name=domain_fixture,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.id == kernel_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


@pytest.fixture()
async def session_seed_no_ports(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session + kernel with ``service_ports=None``.

    Used to test that ``get_stream_apps()`` returns an empty list when
    the kernel has no service ports configured.
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-stream-noports-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=1,
                cluster_mode="single-node",
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_fixture,
                status=SessionStatus.RUNNING,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=kernel_id,
                session_id=session_id,
                session_creation_id=f"cid-{unique}",
                session_name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                cluster_mode="single-node",
                cluster_size=1,
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group=scaling_group_fixture,
                status=KernelStatus.RUNNING,
                status_info="",
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
                service_ports=None,
            )
        )

    yield SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=kernel_id,
        access_key=admin_user_fixture.keypair.access_key,
        domain_name=domain_fixture,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.id == kernel_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )
