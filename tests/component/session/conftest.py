from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.plugin.monitor import ErrorPluginContext
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session.handler import SessionHandler
from ai.backend.manager.api.rest.session.registry import register_session_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.session.service import SessionService, SessionServiceArgs
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors


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


@pytest.fixture()
async def session_processors(
    database_engine: ExtendedAsyncSAEngine,
    agent_registry: AsyncMock,
    background_task_manager: BackgroundTaskManager,
    error_monitor: ErrorPluginContext,
    appproxy_client_pool: AsyncMock,
) -> SessionProcessors:
    """Real SessionProcessors with real SessionService and SessionRepository."""
    session_repo = SessionRepository(database_engine)
    args = SessionServiceArgs(
        agent_registry=agent_registry,
        event_fetcher=AsyncMock(),
        background_task_manager=background_task_manager,
        event_hub=AsyncMock(),
        error_monitor=error_monitor,
        idle_checker_host=AsyncMock(),
        session_repository=session_repo,
        scheduling_controller=AsyncMock(),
        appproxy_client_pool=appproxy_client_pool,
    )
    service = SessionService(args)
    return SessionProcessors(service=service, action_monitors=[])


@pytest.fixture()
def agent_processors_mock() -> AgentProcessors:
    """AgentProcessors with a mocked AgentService."""
    return AgentProcessors(service=AsyncMock(), action_monitors=[])


@pytest.fixture()
def vfolder_processors_mock() -> VFolderProcessors:
    """VFolderProcessors with a mocked VFolderService."""
    return VFolderProcessors(service=AsyncMock(), action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    auth_processors: AuthProcessors,
    session_processors: SessionProcessors,
    agent_processors_mock: AgentProcessors,
    vfolder_processors_mock: VFolderProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for session component tests."""
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
        register_session_routes(
            SessionHandler(
                auth=auth_processors,
                session=session_processors,
                agent=agent_processors_mock,
                vfolder=vfolder_processors_mock,
                config_provider=config_provider,
            ),
            route_deps,
        ),
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
