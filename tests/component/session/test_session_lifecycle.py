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
    GetSessionInfoResponse,
    GetStatusHistoryResponse,
    TransitSessionStatusResponse,
)
from ai.backend.common.types import ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionRow

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
        await admin_registry.session.restart(
            session_seed.session_name,
            RestartSessionRequest(),
        )
        # After restart, session should still be accessible
        result = await admin_registry.session.get_info(session_seed.session_name)
        assert isinstance(result, GetSessionInfoResponse)

    async def test_restart_terminated_session_fails(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        # Terminated sessions are stale and cannot be found for restart
        with pytest.raises((NotFoundError, BackendAPIError)):
            await admin_registry.session.restart(
                terminated_session_seed.session_name,
                RestartSessionRequest(),
            )

    async def test_restart_nonexistent_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.restart(
                "nonexistent-session-xyz-99999",
                RestartSessionRequest(),
            )


class TestSessionStatusTransition:
    """Test session status transit endpoint (POST /_/transit-status)."""

    @pytest.mark.xfail(
        reason="Requires live agent — agent_registry mock does not return proper transit result"
    )
    async def test_transit_single_session_status(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[session_seed.session_id]),
        )
        assert isinstance(result, TransitSessionStatusResponse)
        assert isinstance(result.session_status_map, dict)

    @pytest.mark.xfail(
        reason="Requires live agent — agent_registry mock does not return proper transit result"
    )
    async def test_transit_multiple_sessions(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.transit_session_status(
            TransitSessionStatusRequest(
                ids=[session_seed.session_id, terminated_session_seed.session_id],
            ),
        )
        assert isinstance(result, TransitSessionStatusResponse)
        assert isinstance(result.session_status_map, dict)

    async def test_user_cannot_transit_others_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Regular user cannot transit status of admin-owned sessions.

        The service returns an empty result map for sessions the user does not own.
        """
        result = await user_registry.session.transit_session_status(
            TransitSessionStatusRequest(ids=[session_seed.session_id]),
        )
        assert isinstance(result, TransitSessionStatusResponse)
        # The result should be empty because the user doesn't own this session
        assert session_seed.session_id not in result.session_status_map


class TestSessionRenameLifecycle:
    """Test rename edge cases beyond basic rename already tested in test_session.py."""

    async def test_rename_back_and_forth(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Rename session, then rename back to original name."""
        original_name = session_seed.session_name
        new_name = f"{original_name}-lifecycle-test"

        # Rename to new name
        await admin_registry.session.rename(
            original_name,
            RenameSessionRequest(session_name=new_name),
        )
        result = await admin_registry.session.get_info(new_name)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["status"] == "RUNNING"

        # Rename back to original name
        await admin_registry.session.rename(
            new_name,
            RenameSessionRequest(session_name=original_name),
        )
        result = await admin_registry.session.get_info(original_name)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["status"] == "RUNNING"

    async def test_rename_to_same_name_is_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Renaming a session to the same name is rejected by the server."""
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
        """Regular user can rename their own session."""
        new_name = f"{user_session_seed.session_name}-renamed"
        await user_registry.session.rename(
            user_session_seed.session_name,
            RenameSessionRequest(session_name=new_name),
        )
        result = await user_registry.session.get_info(new_name)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["status"] == "RUNNING"


class TestSessionPermissions:
    """Test role-based access control for session operations."""

    async def test_user_gets_own_session_info(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Regular user can access their own session."""
        result = await user_registry.session.get_info(user_session_seed.session_name)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["status"] == "RUNNING"

    async def test_user_cannot_access_admin_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Regular user cannot access admin-owned sessions."""
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.get_info(session_seed.session_name)

    async def test_admin_cannot_access_user_session_without_ownership(
        self,
        admin_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Admin cannot access user sessions via get_info without matching access key.

        This is a known limitation of the current implementation: the get_info handler
        resolves scope using the requester's own access key, so sessions owned by
        other access keys are not found. This behavior may change in future refactoring.
        """
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info(user_session_seed.session_name)

    async def test_user_cannot_destroy_admin_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Regular user cannot destroy admin-owned sessions."""
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
        """Regular user cannot rename admin-owned sessions."""
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
        """A running session should have PENDING and RUNNING in status history."""
        result = await admin_registry.session.get_status_history(
            session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        # Seeded session has PENDING and RUNNING in status_history
        assert "PENDING" in history
        assert "RUNNING" in history

    async def test_terminated_session_status_history_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        """Terminated (stale) sessions are not found by get_status_history.

        The handler uses get_session_validated with allow_stale=False,
        so terminated sessions return 404.
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
        """Regular user can access status history of their own session."""
        result = await user_registry.session.get_status_history(
            user_session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        history = result.root
        assert isinstance(history, dict)
        assert "RUNNING" in history

    async def test_user_cannot_access_admin_session_status_history(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Regular user cannot access status history of admin-owned session."""
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
    ) -> None:
        """Destroying an already-terminated session succeeds (forced destroy is idempotent)."""
        result = await admin_registry.session.destroy(
            terminated_session_seed.session_name,
            DestroySessionRequest(forced=True),
        )
        assert isinstance(result, DestroySessionResponse)

    async def test_user_destroys_own_session(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Regular user can destroy their own session."""
        result = await user_registry.session.destroy(
            user_session_seed.session_name,
            DestroySessionRequest(forced=True),
        )
        assert isinstance(result, DestroySessionResponse)
