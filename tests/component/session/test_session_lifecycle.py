from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    RestartSessionRequest,
    TransitSessionStatusRequest,
)
from ai.backend.common.dto.manager.session.response import (
    GetStatusHistoryResponse,
    TransitSessionStatusResponse,
)
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow

from .conftest import SessionSeedData, UserFixtureData


def _build_kernel_values(
    *,
    session_id: SessionId,
    unique: str,
    session_name: str,
    cluster_size: int,
    domain_name: str,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
    access_key: str,
    scaling_group: str,
    now: datetime,
) -> dict[str, Any]:
    """Return the common kernel column values shared by all session seed fixtures."""
    return dict(
        session_id=session_id,
        session_creation_id=f"cid-{unique}",
        session_name=session_name,
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode="single-node",
        cluster_size=cluster_size,
        domain_name=domain_name,
        group_id=group_id,
        user_uuid=user_uuid,
        access_key=access_key,
        scaling_group=scaling_group,
        status_info="",
        occupied_slots=ResourceSlot(),
        requested_slots=ResourceSlot(),
        repl_in_port=0,
        repl_out_port=0,
        stdin_port=0,
        stdout_port=0,
        created_at=now,
    )


@pytest.fixture()
async def degraded_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING_DEGRADED session with two kernels (one RUNNING, one ERROR)."""
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-degraded-{unique}"
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
        SessionStatus.RUNNING_DEGRADED.name: now.isoformat(),
    }

    common_kernel = _build_kernel_values(
        session_id=session_id,
        unique=unique,
        session_name=session_name,
        cluster_size=2,
        domain_name=domain_fixture,
        group_id=group_fixture,
        user_uuid=admin_user_fixture.user_uuid,
        access_key=admin_user_fixture.keypair.access_key,
        scaling_group=scaling_group_fixture,
        now=now,
    )

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(SessionRow.__table__).values(
                id=session_id,
                creation_id=f"cid-{unique}",
                name=session_name,
                session_type=SessionTypes.INTERACTIVE,
                cluster_size=2,
                cluster_mode="single-node",
                domain_name=domain_fixture,
                group_id=group_fixture,
                user_uuid=admin_user_fixture.user_uuid,
                access_key=admin_user_fixture.keypair.access_key,
                scaling_group_name=scaling_group_fixture,
                status=SessionStatus.RUNNING_DEGRADED,
                status_info="",
                status_history=status_history,
                occupying_slots=ResourceSlot(),
                requested_slots=ResourceSlot(),
                created_at=now,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=uuid.uuid4(),
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                status=KernelStatus.RUNNING,
                **common_kernel,
            )
        )
        await conn.execute(
            sa.insert(kernels).values(
                id=uuid.uuid4(),
                cluster_role="sub",
                cluster_idx=1,
                cluster_hostname="sub1",
                status=KernelStatus.ERROR,
                **common_kernel,
            )
        )

    yield SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=uuid.UUID(int=0),  # not meaningful for multi-kernel
        access_key=admin_user_fixture.keypair.access_key,
        domain_name=domain_fixture,
        user_uuid=admin_user_fixture.user_uuid,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


@pytest.fixture()
async def full_lifecycle_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    admin_user_fixture: UserFixtureData,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session with a full lifecycle status_history
    (PENDING → SCHEDULED → PREPARING → PULLING → CREATING → RUNNING).
    """
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-full-lifecycle-{unique}"
    kernel_id = uuid.uuid4()
    now = datetime.now(tzutc())

    status_history: dict[str, Any] = {
        SessionStatus.PENDING.name: now.isoformat(),
        SessionStatus.SCHEDULED.name: now.isoformat(),
        SessionStatus.PREPARING.name: now.isoformat(),
        SessionStatus.PULLING.name: now.isoformat(),
        SessionStatus.CREATING.name: now.isoformat(),
        SessionStatus.RUNNING.name: now.isoformat(),
    }

    common_kernel = _build_kernel_values(
        session_id=session_id,
        unique=unique,
        session_name=session_name,
        cluster_size=1,
        domain_name=domain_fixture,
        group_id=group_fixture,
        user_uuid=admin_user_fixture.user_uuid,
        access_key=admin_user_fixture.keypair.access_key,
        scaling_group=scaling_group_fixture,
        now=now,
    )

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
                cluster_role="main",
                cluster_idx=0,
                cluster_hostname="main0",
                status=KernelStatus.RUNNING,
                **common_kernel,
            )
        )

    yield SessionSeedData(
        session_id=session_id,
        session_name=session_name,
        kernel_id=kernel_id,
        access_key=admin_user_fixture.keypair.access_key,
        domain_name=domain_fixture,
        user_uuid=admin_user_fixture.user_uuid,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.session_id == session_id))
        await conn.execute(
            SessionRow.__table__.delete().where(SessionRow.__table__.c.id == session_id)
        )


class TestSessionRestart:
    """Test session restart lifecycle."""

    async def test_restart_running_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin restarts a currently RUNNING session.

        Verifies that the restart API call succeeds and the session
        remains in RUNNING status afterward (i.e., restart is a no-op
        on the status when the agent mock simply acknowledges the request).
        """
        await admin_registry.session.restart(
            session_seed.session_name,
            RestartSessionRequest(),
        )
        result = await admin_registry.session.get_info(session_seed.session_name)
        assert result.root["status"] == SessionStatus.RUNNING.name

    async def test_restart_terminated_session_fails(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin attempts to restart a TERMINATED session.

        Verifies that the server rejects the request because the session
        is stale (allow_stale=False) and cannot be resolved for restart.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await admin_registry.session.restart(
                terminated_session_seed.session_name,
                RestartSessionRequest(),
            )

    async def test_restart_nonexistent_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Scenario: Admin attempts to restart a session that does not exist.

        Verifies that a completely unknown session name results in a
        NotFoundError rather than an unexpected server error.
        """
        with pytest.raises(NotFoundError):
            await admin_registry.session.restart(
                "nonexistent-session-xyz-99999",
                RestartSessionRequest(),
            )


class TestSessionStatusTransition:
    """Test session status transit endpoint (POST /_/transit-status)."""

    @pytest.fixture()
    def session_lifecycle_manager_mock(
        self,
        agent_registry: AsyncMock,
    ) -> AsyncMock:
        """Mock SessionLifecycleManager and attach it to the agent_registry."""
        lifecycle_manager = AsyncMock()
        lifecycle_manager.deregister_status_updatable_session.return_value = None
        agent_registry.session_lifecycle_mgr = lifecycle_manager
        return lifecycle_manager

    async def test_transit_single_session_status(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: Admin triggers status transition for a single RUNNING session.

        Verifies that the transit-status endpoint returns a valid response
        containing the session ID in the status map, confirming that the
        lifecycle manager was invoked and the result was serialized correctly.
        """
        mock_row = AsyncMock()
        mock_row.id = session_seed.session_id
        mock_row.status = SessionStatus.RUNNING
        session_lifecycle_manager_mock.transit_session_status.return_value = [
            (mock_row, False),
        ]
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[session_seed.session_id]),
        )
        assert isinstance(result, TransitSessionStatusResponse)
        assert isinstance(result.session_status_map, dict)
        assert session_seed.session_id in result.session_status_map

    async def test_transit_multiple_sessions(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        terminated_session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: Admin triggers status transition for multiple sessions at once.

        Sends a batch request with both a RUNNING and a TERMINATED session.
        Verifies that the handler iterates over each session ID individually,
        calls the lifecycle manager per session, and aggregates all results
        into a single response map.
        """
        running_row = AsyncMock()
        running_row.id = session_seed.session_id
        running_row.status = SessionStatus.RUNNING

        terminated_row = AsyncMock()
        terminated_row.id = terminated_session_seed.session_id
        terminated_row.status = SessionStatus.TERMINATED

        session_lifecycle_manager_mock.transit_session_status.side_effect = [
            [(running_row, False)],
            [(terminated_row, False)],
        ]
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(
                ids=[session_seed.session_id, terminated_session_seed.session_id],
            ),
        )
        assert isinstance(result, TransitSessionStatusResponse)
        assert isinstance(result.session_status_map, dict)
        assert session_seed.session_id in result.session_status_map
        assert terminated_session_seed.session_id in result.session_status_map

    async def test_transit_reflects_new_status_after_transition(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: Lifecycle manager actually transitions a session (is_transited=True).

        When a kernel status change triggers a valid session transition
        (e.g., RUNNING → TERMINATING), the response status map must reflect
        the NEW status, not the original one.
        """
        mock_row = AsyncMock()
        mock_row.id = session_seed.session_id
        mock_row.status = SessionStatus.TERMINATING
        session_lifecycle_manager_mock.transit_session_status.return_value = [
            (mock_row, True),
        ]
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[session_seed.session_id]),
        )
        assert result.session_status_map[session_seed.session_id] == SessionStatus.TERMINATING.name

    async def test_transit_terminal_session_returns_unchanged_status(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: Transit is requested for a TERMINATED session.

        TERMINATED is a terminal state with no valid outgoing transitions.
        The lifecycle manager returns is_transited=False and the response
        status map should still contain the session with TERMINATED status.
        """
        mock_row = AsyncMock()
        mock_row.id = terminated_session_seed.session_id
        mock_row.status = SessionStatus.TERMINATED
        session_lifecycle_manager_mock.transit_session_status.return_value = [
            (mock_row, False),
        ]
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[terminated_session_seed.session_id]),
        )
        assert (
            result.session_status_map[terminated_session_seed.session_id]
            == SessionStatus.TERMINATED.name
        )

    async def test_deregister_called_only_for_transited_sessions(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        terminated_session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: Batch transit where only some sessions actually transition.

        When one session transitions (RUNNING → TERMINATING) and another
        does not (TERMINATED stays), deregister_status_updatable_session
        must be called only with the transited session's ID.
        """
        transited_row = AsyncMock()
        transited_row.id = session_seed.session_id
        transited_row.status = SessionStatus.TERMINATING

        unchanged_row = AsyncMock()
        unchanged_row.id = terminated_session_seed.session_id
        unchanged_row.status = SessionStatus.TERMINATED

        session_lifecycle_manager_mock.transit_session_status.side_effect = [
            [(transited_row, True)],
            [(unchanged_row, False)],
        ]
        await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(
                ids=[session_seed.session_id, terminated_session_seed.session_id],
            ),
        )
        deregister_calls = (
            session_lifecycle_manager_mock.deregister_status_updatable_session.call_args_list
        )
        deregistered_ids = [session_id for call in deregister_calls for session_id in call.args[0]]
        assert session_seed.session_id in deregistered_ids
        assert terminated_session_seed.session_id not in deregistered_ids

    async def test_user_cannot_transit_others_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user attempts to transit status of an admin-owned session.

        Verifies that the service checks ownership before delegating to the
        lifecycle manager. Since the user does not own the session, the result
        map should be empty (the request succeeds but has no effect).
        """
        result = await user_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[session_seed.session_id]),
        )
        assert isinstance(result, TransitSessionStatusResponse)
        assert session_seed.session_id not in result.session_status_map

    async def test_transit_degraded_session_recovers_to_running(
        self,
        admin_registry: BackendAIClientRegistry,
        degraded_session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: A RUNNING_DEGRADED session recovers to RUNNING.

        When all kernels return to healthy status, the lifecycle manager
        transitions the session from RUNNING_DEGRADED back to RUNNING.
        Verifies that the recovery transition is reflected in the response.
        """
        mock_row = AsyncMock()
        mock_row.id = degraded_session_seed.session_id
        mock_row.status = SessionStatus.RUNNING
        session_lifecycle_manager_mock.transit_session_status.return_value = [
            (mock_row, True),
        ]
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[degraded_session_seed.session_id]),
        )
        assert (
            result.session_status_map[degraded_session_seed.session_id]
            == SessionStatus.RUNNING.name
        )

    async def test_transit_degraded_session_to_terminating(
        self,
        admin_registry: BackendAIClientRegistry,
        degraded_session_seed: SessionSeedData,
        session_lifecycle_manager_mock: AsyncMock,
    ) -> None:
        """Scenario: A RUNNING_DEGRADED session transitions to TERMINATING.

        RUNNING_DEGRADED → TERMINATING is a valid transition in the
        SESSION_STATUS_TRANSITION_MAP. Verifies the endpoint returns the
        new TERMINATING status.
        """
        mock_row = AsyncMock()
        mock_row.id = degraded_session_seed.session_id
        mock_row.status = SessionStatus.TERMINATING
        session_lifecycle_manager_mock.transit_session_status.return_value = [
            (mock_row, True),
        ]
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[degraded_session_seed.session_id]),
        )
        assert (
            result.session_status_map[degraded_session_seed.session_id]
            == SessionStatus.TERMINATING.name
        )


class TestSessionStatusHistory:
    """Test status history for sessions in different lifecycle stages."""

    async def test_running_session_has_pending_and_running_history(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a RUNNING session.

        The seeded session was created with PENDING -> RUNNING transitions.
        Verifies that both status entries are recorded in the history and
        returned by the get_status_history endpoint.
        """
        result = await admin_registry.session.get_status_history(
            session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert SessionStatus.PENDING.name in history
        assert SessionStatus.RUNNING.name in history

    async def test_terminated_session_status_history_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a TERMINATED session.

        The get_status_history handler resolves the session with
        allow_stale=False, so terminated sessions are treated as
        non-existent and return 404. This prevents querying history
        of stale sessions through this endpoint.
        """
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_status_history(
                terminated_session_seed.session_name,
            )

    async def test_user_gets_own_session_status_history(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user queries status history of their own RUNNING session.

        Verifies that the status history endpoint is accessible to
        non-admin users for sessions they own.
        """
        result = await user_registry.session.get_status_history(
            user_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert SessionStatus.RUNNING.name in history

    async def test_user_cannot_access_admin_session_status_history(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user attempts to query status history of an admin-owned session.

        Verifies that ownership scoping applies to the status history
        endpoint — sessions not owned by the requester are not resolvable.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.get_status_history(
                session_seed.session_name,
            )

    async def test_full_lifecycle_status_history(
        self,
        admin_registry: BackendAIClientRegistry,
        full_lifecycle_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a session that went through
        the full scheduling lifecycle (PENDING → SCHEDULED → PREPARING →
        PULLING → CREATING → RUNNING).

        Verifies that every intermediate status is recorded in the history
        with a timestamp, confirming that the status_history column
        accumulates entries across all transitions.
        """
        result = await admin_registry.session.get_status_history(
            full_lifecycle_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        expected_statuses = [
            SessionStatus.PENDING,
            SessionStatus.SCHEDULED,
            SessionStatus.PREPARING,
            SessionStatus.PULLING,
            SessionStatus.CREATING,
            SessionStatus.RUNNING,
        ]
        for status in expected_statuses:
            assert status.name in history, f"{status.name} missing from status history"

    async def test_degraded_session_status_history_includes_degraded(
        self,
        admin_registry: BackendAIClientRegistry,
        degraded_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries status history of a RUNNING_DEGRADED session.

        Verifies that the RUNNING_DEGRADED status is recorded in the history,
        confirming that the transition from RUNNING to RUNNING_DEGRADED was tracked.
        """
        result = await admin_registry.session.get_status_history(
            degraded_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert SessionStatus.RUNNING.name in history
        assert SessionStatus.RUNNING_DEGRADED.name in history
