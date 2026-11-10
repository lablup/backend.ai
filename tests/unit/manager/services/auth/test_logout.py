from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.errors.auth import LoginSessionNotFoundError
from ai.backend.manager.models.login_session.enums import LoginAttemptResult
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.auth.actions.logout import LogoutAction
from ai.backend.manager.services.auth.service import AuthService


class TestLogout:
    @pytest.fixture
    def repository(self) -> AsyncMock:
        repository = AsyncMock(spec=AuthRepository)
        repository.delete_owned_login_session_by_token.return_value = None
        return repository

    @pytest.fixture
    def action(self) -> LogoutAction:
        return LogoutAction(user_id=uuid4(), session_token="session-token")

    @pytest.fixture
    def service(
        self,
        repository: AsyncMock,
        mock_hook_plugin_ctx: MagicMock,
        mock_config_provider: MagicMock,
        mock_user_repository: AsyncMock,
        mock_group_repository: AsyncMock,
        mock_valkey_session_client: AsyncMock,
    ) -> AuthService:
        return AuthService(
            hook_plugin_ctx=mock_hook_plugin_ctx,
            auth_repository=repository,
            config_provider=mock_config_provider,
            valkey_session_client=mock_valkey_session_client,
            user_resource_policy_repository=AsyncMock(spec=UserResourcePolicyRepository),
            user_repository=mock_user_repository,
            group_repository=mock_group_repository,
            ssh_key_validator=AsyncMock(),
        )

    @pytest.fixture
    def missing_owned_session(self, repository: AsyncMock) -> None:
        repository.delete_owned_login_session_by_token.side_effect = LoginSessionNotFoundError()

    async def test_logout_deletes_valkey_session_after_owned_session(
        self,
        service: AuthService,
        repository: AsyncMock,
        action: LogoutAction,
        mock_valkey_session_client: AsyncMock,
    ) -> None:
        result = await service.logout(action)

        assert result.success is True
        repository.delete_owned_login_session_by_token.assert_awaited_once_with(
            action.session_token, action.user_id, LoginAttemptResult.LOGOUT
        )
        mock_valkey_session_client.delete_login_session.assert_awaited_once_with(
            action.session_token
        )

    async def test_logout_rejects_missing_owned_session_without_deleting_valkey(
        self,
        service: AuthService,
        action: LogoutAction,
        missing_owned_session: None,
        mock_valkey_session_client: AsyncMock,
    ) -> None:
        with pytest.raises(LoginSessionNotFoundError):
            await service.logout(action)

        mock_valkey_session_client.delete_login_session.assert_not_awaited()
