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
from ai.backend.manager.api.context import CleanupContext, RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.session.registry import register_session_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
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
async def _session_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for session component tests.

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
    # is never set.  The @server_status_required decorator (used by session
    # handlers) calls config_provider._legacy_etcd_config_loader.get_manager_status()
    # which is async.  Inject a MagicMock with an AsyncMock method so the check passes.
    mock_legacy_loader = MagicMock()
    mock_legacy_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    root_ctx.config_provider._legacy_etcd_config_loader = mock_legacy_loader

    root_ctx.registry = AsyncMock()

    # idle_checker_host.get_idle_check_report() must return a JSON-serializable
    # value; the default AsyncMock return (another AsyncMock object) causes
    # TypeError in web.json_response().
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
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for session component tests."""
    return [register_auth_routes, register_session_routes]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for session component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _session_domain_ctx,
    ]


@pytest.fixture()
async def session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session + kernel directly in the database.

    Since session creation requires a live agent (agent RPC for resource
    allocation and container creation), we bypass the API and insert rows
    directly. This allows testing read/update/error operations through
    the SDK v2 SessionClient.
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-session-{unique}"
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
async def terminated_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a TERMINATED session with container_log in the kernel.

    Used for testing get_container_logs which reads logs from the database
    for terminated sessions (no agent RPC needed).
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-terminated-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
        SessionStatus.TERMINATED.name: now.isoformat(),
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
                status=SessionStatus.TERMINATED,
                status_info="user-requested",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
                terminated_at=now,
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
                status=KernelStatus.TERMINATED,
                status_info="user-requested",
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                created_at=now,
                terminated_at=now,
                container_log=b"Hello from terminated container\n",
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
