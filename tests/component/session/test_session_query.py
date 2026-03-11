"""Component tests for session status history, direct access info, match, and search."""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.exceptions import (
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
)
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.compute_session import (
    SearchComputeSessionsRequest,
    SearchComputeSessionsResponse,
)
from ai.backend.common.dto.manager.compute_session.types import ComputeSessionFilter
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.session.request import MatchSessionsRequest
from ai.backend.common.dto.manager.session.response import (
    GetDirectAccessInfoResponse,
    GetStatusHistoryResponse,
    MatchSessionsResponse,
)
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.api.rest.compute_sessions.handler import ComputeSessionsHandler
from ai.backend.manager.api.rest.compute_sessions.registry import (
    register_compute_sessions_routes,
)

# Statically imported so that Pants includes these modules in the test PEX.
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session.handler import SessionHandler
from ai.backend.manager.api.rest.session.registry import register_session_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.session.processors import SessionProcessors
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors

from .conftest import SessionSeedData, UserFixtureData


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    config_provider: ManagerConfigProvider,
    auth_processors: AuthProcessors,
    session_processors: SessionProcessors,
    agent_processors_mock: AgentProcessors,
    vfolder_processors_mock: VFolderProcessors,
) -> list[RouteRegistry]:
    """Extended module registries including session and compute-sessions routes.

    Overrides the conftest fixture to include ComputeSessionsHandler routes
    required for TestSessionSearch tests.
    """
    return [
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
        register_compute_sessions_routes(
            ComputeSessionsHandler(session=session_processors),
            route_deps,
        ),
    ]


@pytest.fixture()
async def system_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING SYSTEM session with an agent row for direct access info tests.

    Sets up:
    - Agent row with public_host and sshd service port
    - SYSTEM type session
    - Kernel linked to the agent with sshd service_ports
    Used for S-9: SYSTEM session direct access info returns sshd/sftpd ports.
    """
    unique = secrets.token_hex(4)
    agent_id = f"test-agent-{unique}"
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-system-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }
    service_ports = [
        {
            "name": "sshd",
            "protocol": "tcp",
            "container_ports": [22],
            "host_ports": [10022],
        }
    ]

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AgentRow.__table__).values(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=scaling_group_fixture,
                available_slots=ResourceSlot(),
                occupied_slots=ResourceSlot(),
                addr="tcp://127.0.0.1:6001",
                public_host="127.0.0.1",
                version="1.0.0",
                architecture="x86_64",
                compute_plugins={},
            )
        )
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.SYSTEM,
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
                session_type=SessionTypes.SYSTEM,
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
                agent=agent_id,
                agent_addr="tcp://127.0.0.1:6001",
                kernel_host="127.0.0.1",
                service_ports=service_ports,
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
        await conn.execute(AgentRow.__table__.delete().where(AgentRow.__table__.c.id == agent_id))


@pytest.fixture()
async def system_session_no_agent_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING SYSTEM session without an agent row.

    The kernel's agent FK is NULL, so agent_row will be None when loaded.
    Used for F-BIZ-2: Direct access with agent_row=None raises KernelNotReady (HTTP 400).
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-sysnoagent-{unique}"
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
                session_type=SessionTypes.SYSTEM,
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
                session_type=SessionTypes.SYSTEM,
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
                # agent FK intentionally omitted (defaults to NULL)
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
async def second_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
    session_seed: SessionSeedData,
) -> AsyncIterator[SessionSeedData]:
    """Seed a second INTERACTIVE session alongside session_seed.

    Creates a session with a distinct name based on session_seed's name.
    Used for S-12: verifying match_sessions isolates results correctly
    when multiple sessions exist with similar names.
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"{session_seed.session_name}-alt-{unique}"
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


class TestSessionStatusHistory:
    """Tests for GET /{session_name}/status-history."""

    async def test_status_history_has_pending_and_running_entries(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """S-5: Status history retrieval returns dict with PENDING/RUNNING timestamps."""
        result = await admin_registry.session.get_status_history(session_seed.session_name)
        assert isinstance(result, GetStatusHistoryResponse)
        assert isinstance(result.root, dict)
        assert "PENDING" in result.root
        assert "RUNNING" in result.root

    async def test_nonexistent_session_raises_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Nonexistent session raises NotFoundError (HTTP 404)."""
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_status_history("nonexistent-session-xyz-99999")


class TestSessionDirectAccessInfo:
    """Tests for GET /{session_name}/direct-access-info."""

    async def test_interactive_session_returns_empty_dict(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """S-10: INTERACTIVE session direct access info returns empty dict.

        Non-SYSTEM sessions (INTERACTIVE, BATCH) are not in PRIVATE_SESSION_TYPES,
        so direct access info returns an empty response dict without any agent calls.
        """
        result = await admin_registry.session.get_direct_access_info(session_seed.session_name)
        assert isinstance(result, GetDirectAccessInfoResponse)
        assert result.root == {}

    async def test_system_session_returns_sshd_ports(
        self,
        admin_registry: BackendAIClientRegistry,
        system_session_seed: SessionSeedData,
    ) -> None:
        """S-9: SYSTEM session direct access info returns sshd/sftpd ports."""
        result = await admin_registry.session.get_direct_access_info(
            system_session_seed.session_name
        )
        assert isinstance(result, GetDirectAccessInfoResponse)
        assert "sshd_ports" in result.root
        assert "public_host" in result.root
        assert result.root["public_host"] == "127.0.0.1"
        assert result.root["session_type"] == SessionTypes.SYSTEM.name

    async def test_system_session_without_agent_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        system_session_no_agent_seed: SessionSeedData,
    ) -> None:
        """F-BIZ-2: Direct access with agent_row=None raises InvalidRequestError (HTTP 400).

        KernelNotReady inherits from web.HTTPBadRequest, which maps to
        InvalidRequestError in the client SDK.
        """
        with pytest.raises(InvalidRequestError):
            await admin_registry.session.get_direct_access_info(
                system_session_no_agent_seed.session_name
            )


class TestSessionMatchSessions:
    """Tests for GET /_/match."""

    async def test_match_by_session_name_returns_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """S-9: Match sessions by name returns matching sessions.

        The HTTP API uses exact name matching (allow_prefix=False at the db layer).
        Passing the full session name returns the matching session.
        """
        result = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id=session_seed.session_name)
        )
        assert isinstance(result, MatchSessionsResponse)
        matched_ids = [str(m["id"]) for m in result.matches]
        assert str(session_seed.session_id) in matched_ids

    async def test_match_by_session_id_returns_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """S-10: Match sessions by session ID returns matching session.

        Passing the full UUID string triggers exact UUID match in the db layer
        (UUID parsing succeeds, then exact ID match is tried first).
        """
        result = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id=str(session_seed.session_id))
        )
        assert isinstance(result, MatchSessionsResponse)
        assert len(result.matches) == 1
        assert str(result.matches[0]["id"]) == str(session_seed.session_id)

    async def test_match_with_multiple_sessions_returns_only_exact_match(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        second_session_seed: SessionSeedData,
    ) -> None:
        """S-12: When multiple sessions exist, match by exact name returns only the correct one.

        The HTTP API uses exact name matching (allow_prefix=False). Even when another
        session with a similar name exists, only the exactly-named session is returned.
        Prefix-based multi-match is tested at the unit test level.
        """
        result = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id=session_seed.session_name)
        )
        assert isinstance(result, MatchSessionsResponse)
        matched_ids = [str(m["id"]) for m in result.matches]
        assert str(session_seed.session_id) in matched_ids
        assert str(second_session_seed.session_id) not in matched_ids

    async def test_match_filters_by_owner_access_key(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """S-13: owner_access_key filtering — regular user cannot see admin's sessions.

        The match_sessions endpoint resolves owner_access_key to the caller's own access key.
        A regular user searching for an admin-owned session gets empty results.
        """
        result = await user_registry.session.match_sessions(
            MatchSessionsRequest(id=session_seed.session_name)
        )
        assert isinstance(result, MatchSessionsResponse)
        assert len(result.matches) == 0


class TestSessionSearch:
    """Tests for POST /compute-sessions/search.

    This endpoint requires superadmin_required middleware and is served by
    ComputeSessionsHandler (registered via the local server_module_registries override).
    """

    async def test_basic_search_returns_data_and_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """S-1: Basic session search via compute_session returns data + pagination."""
        result = await admin_registry.compute_session.search_sessions(
            SearchComputeSessionsRequest()
        )
        assert isinstance(result, SearchComputeSessionsResponse)
        assert isinstance(result.items, list)
        assert len(result.items) >= 1
        assert result.pagination.total >= 1
        session_ids = [str(item.id) for item in result.items]
        assert str(session_seed.session_id) in session_ids

    async def test_search_with_no_matching_sessions_returns_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-5: Search with filter that matches no sessions returns empty data, total=0."""
        result = await admin_registry.compute_session.search_sessions(
            SearchComputeSessionsRequest(
                filter=ComputeSessionFilter(
                    name=StringFilter(equals="nonexistent-session-xyz-999999999")
                )
            )
        )
        assert isinstance(result, SearchComputeSessionsResponse)
        assert result.items == []
        assert result.pagination.total == 0

    async def test_regular_user_search_is_forbidden(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-AUTH-2: Regular user search attempt is restricted by superadmin_required.

        The compute-sessions/search endpoint has superadmin_required middleware,
        so a regular user receives HTTP 403 Forbidden.
        """
        with pytest.raises(PermissionDeniedError):
            await user_registry.compute_session.search_sessions(SearchComputeSessionsRequest())
