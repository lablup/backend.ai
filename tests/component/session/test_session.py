from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.session.request import (
    DestroySessionRequest,
    MatchSessionsRequest,
    RenameSessionRequest,
)
from ai.backend.common.dto.manager.session.response import (
    DestroySessionResponse,
    GetContainerLogsResponse,
    GetSessionInfoResponse,
    GetStatusHistoryResponse,
    MatchSessionsResponse,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.scheduler.types.session import MarkTerminatingResult

from .conftest import SessionSeedData


class TestSessionGetInfo:
    async def test_admin_gets_session_info(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.get_info(session_seed.session_name)
        assert isinstance(result, GetSessionInfoResponse)
        # LegacySessionInfo.asdict() uses camelCase keys and does not include
        # session id/name — verify that the returned dict contains expected
        # fields from the seeded row instead.
        assert result.root["status"] == SessionStatus.RUNNING.name
        assert result.root["domainName"] == session_seed.domain_name

    async def test_get_nonexistent_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info("nonexistent-session-xyz-99999")


class TestSessionRename:
    async def test_admin_renames_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        new_name = f"{session_seed.session_name}-renamed"
        await admin_registry.session.rename(
            session_seed.session_name,
            RenameSessionRequest(session_name=new_name),
        )
        # Verify the rename took effect by fetching with the new name
        result = await admin_registry.session.get_info(new_name)
        assert isinstance(result, GetSessionInfoResponse)
        assert result.root["status"] == SessionStatus.RUNNING.name

    async def test_rename_nonexistent_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.rename(
                "nonexistent-session-xyz-99999",
                RenameSessionRequest(session_name="new-name"),
            )

    async def test_rename_back_and_forth(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Verifies that rename is fully reversible — after each rename the new name
        resolves successfully while the old name returns NotFoundError.
        """
        original_name = session_seed.session_name
        new_name = f"{original_name}-lifecycle-test"

        await admin_registry.session.rename(
            original_name,
            RenameSessionRequest(session_name=new_name),
        )
        result = await admin_registry.session.get_info(new_name)
        assert result.root["status"] == SessionStatus.RUNNING.name
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info(original_name)

        await admin_registry.session.rename(
            new_name,
            RenameSessionRequest(session_name=original_name),
        )
        result = await admin_registry.session.get_info(original_name)
        assert result.root["status"] == SessionStatus.RUNNING.name
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_info(new_name)

    async def test_rename_to_same_name_is_rejected(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """The server rejects a no-op rename as an invalid request
        rather than silently succeeding.
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
        """Non-admin users have rename permission on sessions they own,
        and the old name is no longer resolvable after rename.
        """
        original_name = user_session_seed.session_name
        new_name = f"{original_name}-renamed"
        await user_registry.session.rename(
            original_name,
            RenameSessionRequest(session_name=new_name),
        )
        result = await user_registry.session.get_info(new_name)
        assert result.root["status"] == SessionStatus.RUNNING.name
        with pytest.raises(NotFoundError):
            await user_registry.session.get_info(original_name)


class TestSessionMatchSessions:
    async def test_admin_matches_sessions_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id=session_seed.session_name),
        )
        assert isinstance(result, MatchSessionsResponse)
        assert len(result.matches) >= 1
        matched_ids = [str(m["id"]) for m in result.matches]
        assert str(session_seed.session_id) in matched_ids

    async def test_match_returns_empty_for_unknown_name(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id="nonexistent-session-xyz-99999"),
        )
        assert isinstance(result, MatchSessionsResponse)
        assert len(result.matches) == 0


class TestSessionGetStatusHistory:
    async def test_admin_gets_status_history(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.get_status_history(
            session_seed.session_name,
        )
        assert isinstance(result, GetStatusHistoryResponse)
        # The result dict should contain status history entries
        assert isinstance(result.root, dict)

    async def test_get_status_history_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_status_history(
                "nonexistent-session-xyz-99999",
            )


class TestSessionDestroy:
    async def test_admin_destroys_session(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.destroy(
            session_seed.session_name,
            DestroySessionRequest(forced=True),
        )
        assert isinstance(result, DestroySessionResponse)

    async def test_destroy_nonexistent_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.destroy(
                "nonexistent-session-xyz-99999",
                DestroySessionRequest(forced=True),
            )

    async def test_destroy_already_terminated_session_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
        scheduling_controller_mock: AsyncMock,
    ) -> None:
        """Forced destroy is idempotent — calling destroy on an already-terminated
        session does not raise an error and returns status "terminated".
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
        """Non-admin users have destroy permission on sessions they own."""
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


class TestSessionGetContainerLogs:
    async def test_admin_gets_container_logs_for_terminated_session(
        self,
        admin_registry: BackendAIClientRegistry,
        terminated_session_seed: SessionSeedData,
    ) -> None:
        result = await admin_registry.session.get_container_logs(
            terminated_session_seed.session_name,
        )
        assert isinstance(result, GetContainerLogsResponse)
        assert isinstance(result.root, dict)

    async def test_get_container_logs_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_container_logs(
                "nonexistent-session-xyz-99999",
            )


class TestSessionPermissions:
    """Test role-based access control for session operations."""

    async def test_user_gets_own_session_info(
        self,
        user_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """Users can read their own session metadata including
        status and domain name through the get_info endpoint.
        """
        result = await user_registry.session.get_info(user_session_seed.session_name)
        assert result.root["status"] == SessionStatus.RUNNING.name
        assert result.root["domainName"] == user_session_seed.domain_name

    async def test_user_cannot_access_admin_session(
        self,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Session visibility is scoped by access key — a user keypair
        cannot resolve sessions belonging to a different keypair.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.get_info(session_seed.session_name)

    async def test_admin_cannot_access_user_session_without_ownership(
        self,
        admin_registry: BackendAIClientRegistry,
        user_session_seed: SessionSeedData,
    ) -> None:
        """The get_info handler resolves scope using the requester's own access
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
        """The destroy endpoint enforces ownership — the session is not
        resolvable under the user's access key scope.
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
        """The rename endpoint enforces ownership — the session is not
        resolvable under the user's access key scope.
        """
        with pytest.raises((NotFoundError, BackendAPIError)):
            await user_registry.session.rename(
                session_seed.session_name,
                RenameSessionRequest(session_name="hacked-name"),
            )
