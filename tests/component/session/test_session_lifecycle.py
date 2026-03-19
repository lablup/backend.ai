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
    DestroySessionRequest,
    RenameSessionRequest,
    RestartSessionRequest,
    TransitSessionStatusRequest,
)
from ai.backend.common.dto.manager.session.response import (
    DestroySessionResponse,
    GetStatusHistoryResponse,
    TransitSessionStatusResponse,
)
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.repositories.scheduler.types.session import MarkTerminatingResult

from .conftest import SessionSeedData


@pytest.fixture()
async def user_session_seed(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    regular_user_fixture: Any,
    scaling_group_fixture: str,
) -> AsyncIterator[SessionSeedData]:
    """Seed a RUNNING session owned by the regular user."""
    unique = secrets.token_hex(4)
    session_id = SessionId(uuid.uuid4())
    session_name = f"test-user-session-{unique}"
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
                user_uuid=regular_user_fixture.user_uuid,
                access_key=regular_user_fixture.keypair.access_key,
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
                user_uuid=regular_user_fixture.user_uuid,
                access_key=regular_user_fixture.keypair.access_key,
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
        access_key=regular_user_fixture.keypair.access_key,
        domain_name=domain_fixture,
        user_uuid=regular_user_fixture.user_uuid,
    )

    async with db_engine.begin() as conn:
        await conn.execute(kernels.delete().where(kernels.c.id == kernel_id))
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
        assert result.root["status"] == "RUNNING"

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


class TestSessionRenameLifecycle:
    """Test rename edge cases beyond basic rename already tested in test_session.py."""

    async def test_rename_back_and_forth(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin renames a session to a new name, then reverts to the original.

        Verifies that rename is fully reversible — after each rename the new name
        resolves successfully while the old name returns NotFoundError.
        """
        original_name = session_seed.session_name
        new_name = f"{original_name}-lifecycle-test"

        await admin_registry.session.rename(
            original_name,
            RenameSessionRequest(session_name=new_name),
        )
        result = await admin_registry.session.get_info(new_name)
        assert result.root["status"] == "RUNNING"
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info(original_name)

        await admin_registry.session.rename(
            new_name,
            RenameSessionRequest(session_name=original_name),
        )
        result = await admin_registry.session.get_info(original_name)
        assert result.root["status"] == "RUNNING"
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info(new_name)

    async def test_rename_to_same_name_is_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin attempts to rename a session to its current name.

        Verifies that the server rejects a no-op rename as an invalid
        request rather than silently succeeding.
        """
        with pytest.raises(BackendAPIError):
            await admin_registry.session.rename(
                session_seed.session_name,
                RenameSessionRequest(session_name=session_seed.session_name),
            )

    async def test_user_renames_own_session(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user renames their own session.

        Verifies that non-admin users have rename permission on sessions
        they own, and that the old name is no longer resolvable after rename.
        """
        original_name = user_session_seed.session_name
        new_name = f"{original_name}-renamed"
        await user_registry.session.rename(
            original_name,
            RenameSessionRequest(session_name=new_name),
        )
        result = await user_registry.session.get_info(new_name)
        assert result.root["status"] == "RUNNING"
        with pytest.raises(NotFoundError):
            await user_registry.session.get_info(original_name)


class TestSessionPermissions:
    """Test role-based access control for session operations."""

    async def test_user_gets_own_session_info(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user queries info of their own RUNNING session.

        Verifies that users can read their own session metadata including
        status and domain name through the get_info endpoint.
        """
        result = await user_registry.session.get_info(user_session_seed.session_name)
        assert result.root["status"] == "RUNNING"
        assert result.root["domainName"] == user_session_seed.domain_name

    async def test_user_cannot_access_admin_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user attempts to query an admin-owned session.

        Verifies that session visibility is scoped by access key — a user
        keypair cannot resolve sessions belonging to a different keypair.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.get_info(session_seed.session_name)

    async def test_admin_cannot_access_user_session_without_ownership(
        self,
        admin_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Admin queries a session owned by a regular user's keypair.

        The get_info handler resolves scope using the requester's own access
        key, so sessions owned by other access keys are not found. This is a
        known limitation of the current implementation that may change in
        future refactoring.
        """
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info(user_session_seed.session_name)

    async def test_user_cannot_destroy_admin_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user attempts to force-destroy an admin-owned session.

        Verifies that the destroy endpoint enforces ownership — the session
        is not resolvable under the user's access key scope.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.destroy(
                session_seed.session_name,
                DestroySessionRequest(forced=True),
            )

    async def test_user_cannot_rename_admin_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Scenario: Regular user attempts to rename an admin-owned session.

        Verifies that the rename endpoint enforces ownership — the session
        is not resolvable under the user's access key scope.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.rename(
                session_seed.session_name,
                RenameSessionRequest(session_name="hacked-name"),
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


class TestSessionDestroyLifecycle:
    """Test destroy edge cases for session lifecycle."""

    async def test_destroy_already_terminated_session_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
        scheduling_controller_mock: AsyncMock,
    ) -> None:
        """Scenario: Admin force-destroys a session that is already TERMINATED.

        Verifies that forced destroy is idempotent — calling destroy on an
        already-terminated session does not raise an error and returns a
        valid response with status "terminated".
        """
        scheduling_controller_mock.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[],
                force_terminated_sessions=[terminated_session_seed.session_id],
                skipped_sessions=[],
            )
        )
        result = await admin_registry.session.destroy(
            terminated_session_seed.session_name,
            DestroySessionRequest(forced=True),
        )
        assert isinstance(result, DestroySessionResponse)
        assert result.root["stats"]["status"] == "terminated"

    async def test_user_destroys_own_session(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
        scheduling_controller_mock: AsyncMock,
    ) -> None:
        """Scenario: Regular user force-destroys their own RUNNING session.

        Verifies that non-admin users have destroy permission on sessions
        they own, and that the scheduling controller correctly marks the
        session for termination.
        """
        scheduling_controller_mock.mark_sessions_for_termination.return_value = (
            MarkTerminatingResult(
                cancelled_sessions=[],
                terminating_sessions=[],
                force_terminated_sessions=[user_session_seed.session_id],
                skipped_sessions=[],
            )
        )
        result = await user_registry.session.destroy(
            user_session_seed.session_name,
            DestroySessionRequest(forced=True),
        )
        assert isinstance(result, DestroySessionResponse)
        assert result.root["stats"]["status"] == "terminated"
