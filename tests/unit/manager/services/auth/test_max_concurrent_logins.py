"""Tests for max_concurrent_logins enforcement in AuthService._create_login_session."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.common.exception import UserResourcePolicyNotFound
from ai.backend.manager.config.unified import AuthConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.errors.auth import TooManyConcurrentLoginSessions
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.db_source.db_source import LoginSessionCreationResult
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.auth.actions.authorize import AuthorizeAction
from ai.backend.manager.services.auth.service import AuthService

_DEFAULT_USER_UUID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_DEFAULT_RESOURCE_POLICY = "default"


def _make_auth_config() -> AuthConfig:
    return AuthConfig(
        max_password_age=timedelta(days=90),
        password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        password_hash_rounds=100_000,
        password_hash_salt_size=32,
        login_session_max_age=604800,
    )


def _make_mock_user(resource_policy: str = _DEFAULT_RESOURCE_POLICY) -> MagicMock:
    """Create a minimal mock user RowMapping for _create_login_session."""
    mock_user = MagicMock()
    mock_user.uuid = _DEFAULT_USER_UUID
    mock_user.resource_policy = resource_policy
    mock_user.role = UserRole.USER
    mock_user.status = UserStatus.ACTIVE
    mock_user.__getitem__ = lambda self, key: getattr(self, key)
    return mock_user


def _make_mock_keypair_row(max_concurrent_sessions: int = 5) -> MagicMock:
    """Create a mock keypair row."""
    mock_keypair = MagicMock()
    mock_keypair.access_key = "AKIAIOSFODNN7EXAMPLE"
    mock_keypair.secret_key = "secret"
    mock_keypair.resource_policy_row.max_concurrent_sessions = max_concurrent_sessions
    return mock_keypair


def _make_action() -> AuthorizeAction:
    return AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="user@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )


def _make_policy(max_concurrent_logins: int | None) -> UserResourcePolicyData:
    return UserResourcePolicyData(
        name=_DEFAULT_RESOURCE_POLICY,
        max_vfolder_count=10,
        max_quota_scope_size=0,
        max_session_count_per_model_session=5,
        max_customized_image_count=3,
        max_concurrent_logins=max_concurrent_logins,
    )


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    repo = AsyncMock(spec=AuthRepository)
    repo.create_login_session.return_value = LoginSessionCreationResult(
        session_token="test_session_token",
    )
    return repo


@pytest.fixture
def mock_user_resource_policy_repository() -> AsyncMock:
    return AsyncMock(spec=UserResourcePolicyRepository)


@pytest.fixture
def mock_valkey_session_client() -> AsyncMock:
    return AsyncMock(spec=ValkeySessionClient)


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: MagicMock,
    mock_valkey_session_client: AsyncMock,
    mock_user_resource_policy_repository: AsyncMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
        valkey_session_client=mock_valkey_session_client,
        user_resource_policy_repository=mock_user_resource_policy_repository,
    )


class TestMaxConcurrentLoginsEnforcement:
    """Tests for the max_concurrent_logins enforcement logic in _create_login_session."""

    async def test_limit_1_with_1_active_session_raises(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
    ) -> None:
        """limit=1, user has 1 active login session → new login raises TooManyConcurrentLoginSessions."""
        mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
            max_concurrent_logins=1
        )
        mock_auth_repository.count_active_login_sessions.return_value = 1

        with pytest.raises(TooManyConcurrentLoginSessions):
            await auth_service._create_login_session(
                action=_make_action(),
                user=_make_mock_user(),
                keypair_row=_make_mock_keypair_row(),
                live_sessions=[],
                auth_config=_make_auth_config(),
            )

    async def test_limit_1_with_0_active_sessions_succeeds(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
    ) -> None:
        """limit=1, user has 0 active login sessions → new login succeeds."""
        mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
            max_concurrent_logins=1
        )
        mock_auth_repository.count_active_login_sessions.return_value = 0

        result = await auth_service._create_login_session(
            action=_make_action(),
            user=_make_mock_user(),
            keypair_row=_make_mock_keypair_row(),
            live_sessions=[],
            auth_config=_make_auth_config(),
        )

        assert result.authorization_result is not None

    async def test_limit_none_unlimited_does_not_enforce(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
    ) -> None:
        """limit=None (unlimited sentinel) → no enforcement regardless of session count."""
        mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
            max_concurrent_logins=None
        )
        # Simulate many active sessions — should never be queried
        mock_auth_repository.count_active_login_sessions.return_value = 9999

        result = await auth_service._create_login_session(
            action=_make_action(),
            user=_make_mock_user(),
            keypair_row=_make_mock_keypair_row(),
            live_sessions=[],
            auth_config=_make_auth_config(),
        )

        # count_active_login_sessions must NOT be called when limit is None
        mock_auth_repository.count_active_login_sessions.assert_not_awaited()
        assert result.authorization_result is not None

    async def test_missing_resource_policy_does_not_raise(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
    ) -> None:
        """User with no resolvable resource policy → no enforcement, login succeeds."""
        mock_user_resource_policy_repository.get_by_name.side_effect = UserResourcePolicyNotFound(
            "Policy not found"
        )

        # Should not raise — policy not found means skip enforcement
        result = await auth_service._create_login_session(
            action=_make_action(),
            user=_make_mock_user(),
            keypair_row=_make_mock_keypair_row(),
            live_sessions=[],
            auth_config=_make_auth_config(),
        )

        mock_auth_repository.count_active_login_sessions.assert_not_awaited()
        assert result.authorization_result is not None

    async def test_limit_5_with_5_active_sessions_raises(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
    ) -> None:
        """limit=5, user has 5 active sessions → raises TooManyConcurrentLoginSessions."""
        mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
            max_concurrent_logins=5
        )
        mock_auth_repository.count_active_login_sessions.return_value = 5

        with pytest.raises(TooManyConcurrentLoginSessions):
            await auth_service._create_login_session(
                action=_make_action(),
                user=_make_mock_user(),
                keypair_row=_make_mock_keypair_row(),
                live_sessions=[],
                auth_config=_make_auth_config(),
            )

    async def test_limit_5_with_4_active_sessions_succeeds(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        mock_user_resource_policy_repository: AsyncMock,
    ) -> None:
        """limit=5, user has 4 active sessions → succeeds (below limit)."""
        mock_user_resource_policy_repository.get_by_name.return_value = _make_policy(
            max_concurrent_logins=5
        )
        mock_auth_repository.count_active_login_sessions.return_value = 4

        result = await auth_service._create_login_session(
            action=_make_action(),
            user=_make_mock_user(),
            keypair_row=_make_mock_keypair_row(),
            live_sessions=[],
            auth_config=_make_auth_config(),
        )

        assert result.authorization_result is not None
