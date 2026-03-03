from __future__ import annotations

import pytest

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
        assert result.root["status"] == "RUNNING"
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
        assert result.root["status"] == "RUNNING"

    async def test_rename_nonexistent_session_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.rename(
                "nonexistent-session-xyz-99999",
                RenameSessionRequest(session_name="new-name"),
            )


class TestSessionMatchSessions:
    @pytest.mark.xfail(
        strict=False,
        reason="match_sessions query param conflicts with HMAC signing - SDK signing bug",
    )
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

    @pytest.mark.xfail(
        strict=False,
        reason="match_sessions query param conflicts with HMAC signing - SDK signing bug",
    )
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
        assert isinstance(result.result, dict)

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
        assert isinstance(result.result, dict)

    async def test_get_container_logs_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.session.get_container_logs(
                "nonexistent-session-xyz-99999",
            )
