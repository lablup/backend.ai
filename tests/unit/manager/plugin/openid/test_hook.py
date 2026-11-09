from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import jwt
import pytest
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.auth.types import AuthorizingUser
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.plugin.openid.hook import OIDCHookPlugin
from ai.backend.manager.repositories.auth.repository import AuthRepository


class TestOIDCHookPlugin:
    @pytest.fixture
    def active_user(self) -> MagicMock:
        return MagicMock(
            spec=AuthorizingUser,
            uuid=uuid4(),
            email="user@example.com",
            status=UserStatus.ACTIVE,
        )

    @pytest.fixture
    def auth_repository(self, active_user: MagicMock) -> MagicMock:
        repository = MagicMock(spec=AuthRepository)
        repository.query_user_data = AsyncMock(return_value=active_user)
        repository.invalidate_active_login_sessions = AsyncMock(
            return_value=["first-session-token", "second-session-token"]
        )
        return repository

    @pytest.fixture
    def valkey_session(self) -> MagicMock:
        return MagicMock(spec=ValkeySessionClient)

    @pytest.fixture
    def request_with_sessions(
        self, auth_repository: MagicMock, valkey_session: MagicMock
    ) -> MagicMock:
        request = MagicMock(spec=web.Request)
        request.app = {
            "_root_app": {
                "_auth_repository": auth_repository,
                "_valkey_session": valkey_session,
            },
        }
        return request

    async def test_force_login_deletes_invalidated_sessions_from_valkey(
        self,
        active_user: MagicMock,
        auth_repository: MagicMock,
        valkey_session: MagicMock,
        request_with_sessions: MagicMock,
    ) -> None:
        secret = "test-openid-signing-secret-with-32-bytes"
        plugin = OIDCHookPlugin({"secret": secret}, {})
        token = jwt.encode(
            {"user": str(active_user.uuid), "email": active_user.email, "force": True},
            secret,
            algorithm="HS256",
        )

        user = await plugin.pre_auth_hook(request_with_sessions, {"stoken": token})

        assert user is active_user
        auth_repository.invalidate_active_login_sessions.assert_awaited_once_with(
            UserID(active_user.uuid)
        )
        valkey_session.delete_login_sessions.assert_awaited_once_with([
            "first-session-token",
            "second-session-token",
        ])
