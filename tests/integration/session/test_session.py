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
    GetSessionInfoResponse,
    GetStatusHistoryResponse,
    MatchSessionsResponse,
)

from .conftest import SessionSeedData


@pytest.mark.integration
class TestSessionLifecycle:
    async def test_session_read_and_update_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """seed -> get_info -> rename -> get_info (verify rename) -> match -> status_history -> destroy"""
        # 1. get_info
        info_result = await admin_registry.session.get_info(session_seed.session_name)
        assert isinstance(info_result, GetSessionInfoResponse)
        # LegacySessionInfo.asdict() uses camelCase keys and does not include
        # session id/name — verify via fields that are present.
        assert info_result.root["status"] == "RUNNING"
        assert info_result.root["domainName"] == session_seed.domain_name

        # 2. rename
        new_name = f"{session_seed.session_name}-renamed"
        await admin_registry.session.rename(
            session_seed.session_name,
            RenameSessionRequest(session_name=new_name),
        )

        # 3. get_info again to verify rename (fetching by new name succeeds)
        renamed_result = await admin_registry.session.get_info(new_name)
        assert isinstance(renamed_result, GetSessionInfoResponse)
        assert renamed_result.root["status"] == "RUNNING"
        assert renamed_result.root["domainName"] == session_seed.domain_name

        # 4. match_sessions
        match_result = await admin_registry.session.match_sessions(
            MatchSessionsRequest(id=new_name),
        )
        assert isinstance(match_result, MatchSessionsResponse)
        assert len(match_result.matches) >= 1

        # 5. status_history
        history_result = await admin_registry.session.get_status_history(new_name)
        assert isinstance(history_result, GetStatusHistoryResponse)
        assert isinstance(history_result.root, dict)

        # 6. destroy (forced, since no real agent to handle graceful shutdown)
        destroy_result = await admin_registry.session.destroy(
            new_name,
            DestroySessionRequest(forced=True),
        )
        assert isinstance(destroy_result, DestroySessionResponse)


@pytest.mark.integration
class TestSessionPermissions:
    async def test_regular_user_denied_admin_session_operations(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Verify PermissionDenied or NotFound for regular user on admin's session.

        Session access control returns ObjectNotFound (rather than
        PermissionDenied) when the user cannot see the session at all,
        because sessions are scoped by access_key/user ownership.
        """
        # get_info — user cannot see admin's session
        with pytest.raises(NotFoundError):
            await user_registry.session.get_info(session_seed.session_name)

        # rename — user cannot see admin's session
        with pytest.raises(NotFoundError):
            await user_registry.session.rename(
                session_seed.session_name,
                RenameSessionRequest(session_name="denied-rename"),
            )

        # destroy — user cannot see admin's session
        with pytest.raises(NotFoundError):
            await user_registry.session.destroy(
                session_seed.session_name,
                DestroySessionRequest(forced=True),
            )
