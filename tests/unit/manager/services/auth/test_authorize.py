from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.dto.manager.auth.types import AuthTokenType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.plugin.hook import HookPluginContext, HookResult, HookResults
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import AuthConfig, ManagerConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.auth import AuthorizationFailed, PasswordExpired
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.db_source.db_source import (
    ActiveSessionInfo,
    CredentialVerificationResult,
    LoginSessionCreationResult,
)
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.authorize import (
    AuthorizeAction,
)
from ai.backend.manager.services.auth.service import AuthService

_DEFAULT_USER_UUID = UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_hook_plugin_ctx() -> MagicMock:
    return MagicMock(spec=HookPluginContext)


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_provider.config = MagicMock(spec=ManagerConfig)
    mock_provider.config.auth = AuthConfig(
        max_password_age=timedelta(days=90),
        password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        password_hash_rounds=100_000,
        password_hash_salt_size=32,
        login_session_max_age=604800,
    )
    return mock_provider


@pytest.fixture
def mock_valkey_session_client() -> AsyncMock:
    return AsyncMock(spec=ValkeySessionClient)


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: MagicMock,
    mock_valkey_session_client: AsyncMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
        valkey_session_client=mock_valkey_session_client,
    )


def _make_mock_user(
    *,
    uuid: UUID = _DEFAULT_USER_UUID,
    email: str = "test@example.com",
    role: UserRole = UserRole.USER,
    status: UserStatus = UserStatus.ACTIVE,
    password_changed_at: datetime | None = None,
) -> MagicMock:
    """Create a mock user RowMapping with attribute and item access."""
    mock_user = MagicMock()
    mock_user.uuid = uuid
    mock_user.email = email
    mock_user.role = role
    mock_user.status = status
    mock_user.password_changed_at = password_changed_at
    mock_user.__getitem__ = lambda self, key: getattr(self, key)
    return mock_user


def _make_mock_keypair_row(
    *,
    access_key: str = "test_access_key",
    secret_key: str = "test_secret_key",
    max_concurrent_sessions: int = 1,
) -> MagicMock:
    """Create a mock keypair row with access_key, secret_key, and mapping."""
    mock_keypair = MagicMock()
    mock_keypair.access_key = access_key
    mock_keypair.secret_key = secret_key
    mock_keypair.mapping = {"access_key": access_key}
    mock_keypair.resource_policy_row.max_concurrent_sessions = max_concurrent_sessions
    return mock_keypair


@pytest.fixture
def setup_successful_auth(
    mock_auth_repository: AsyncMock,
    mock_hook_plugin_ctx: MagicMock,
    mock_valkey_session_client: AsyncMock,
) -> None:
    """Set up mocks for a successful authorization flow.

    The authorize flow calls:
      1. _verify_user: dispatch AUTHORIZE hook, then verify_credential
      2. _post_check: user status checks, get_user_row_by_uuid, dispatch POST_AUTHORIZE hook,
         Valkey cross-check of active sessions
      3. _create_login_session: create_login_session in DB, set_login_session in Valkey
    """
    # Both AUTHORIZE and POST_AUTHORIZE hooks pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )

    mock_user = _make_mock_user()

    # Step 1: verify_credential returns user with no active sessions
    mock_auth_repository.verify_credential.return_value = CredentialVerificationResult(
        user=mock_user,
        active_sessions=[],
    )

    # Step 2: get_user_row_by_uuid returns a user row with a main keypair
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = _make_mock_keypair_row()
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row

    # Step 3: create_login_session returns the session token
    mock_auth_repository.create_login_session.return_value = LoginSessionCreationResult(
        session_token="test_session_token",
    )

    # Valkey set_login_session is an AsyncMock by default (no extra setup needed)


async def test_authorize_success(
    auth_service: AuthService,
    setup_successful_auth: None,
) -> None:
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="correct_password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    result = await auth_service.authorize(action)

    assert result.authorization_result is not None
    assert result.authorization_result.access_key == "test_access_key"
    assert result.authorization_result.secret_key == "test_secret_key"
    assert result.authorization_result.session_token == "test_session_token"


async def test_authorize_invalid_token_type(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
) -> None:
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )

    action = AuthorizeAction(
        type=AuthTokenType.JWT,
        domain_name="default",
        email="test@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    with pytest.raises(InvalidAPIParameters):
        await auth_service.authorize(action)


async def test_authorize_invalid_credentials(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
) -> None:
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )
    mock_auth_repository.verify_credential.side_effect = AuthorizationFailed(
        "User credential mismatch."
    )

    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="wrong_password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    with pytest.raises(AuthorizationFailed):
        await auth_service.authorize(action)


async def test_authorize_with_hook_authorization(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_valkey_session_client: AsyncMock,
) -> None:
    """Test authorization when AUTHORIZE hook provides the user directly."""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="hook@example.com",
        password="any_password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    # Hook returns user data directly (bypasses verify_credential)
    hook_user = _make_mock_user(
        uuid=UUID("87654321-4321-8765-4321-876543218765"),
        email="hook@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )

    # First call (AUTHORIZE): returns the user
    # Second call (POST_AUTHORIZE): passes normally
    mock_hook_plugin_ctx.dispatch.side_effect = [
        HookResult(status=HookResults.PASSED, result=hook_user, reason=None),
        HookResult(status=HookResults.PASSED, result=None, reason=None),
    ]

    # When hook provides user, _verify_user calls get_active_session_tokens
    mock_auth_repository.get_active_session_tokens.return_value = []

    # Mock user row with keypair
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = _make_mock_keypair_row(
        access_key="hook_access_key",
        secret_key="hook_secret_key",
    )
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row

    # create_login_session returns session token
    mock_auth_repository.create_login_session.return_value = LoginSessionCreationResult(
        session_token="hook_session_token",
    )

    result = await auth_service.authorize(action)

    assert result.authorization_result is not None
    assert result.authorization_result.access_key == "hook_access_key"
    assert result.authorization_result.secret_key == "hook_secret_key"
    assert result.authorization_result.user_id == hook_user.uuid
    assert result.authorization_result.role == UserRole.ADMIN


async def test_authorize_with_password_expiry(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
) -> None:
    """Test authorization fails when password is expired."""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="expired@example.com",
        password="old_password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    # Setup expired password (changed 100 days ago, max age is 90 days)
    password_changed_at = datetime.now(tz=UTC) - timedelta(days=100)
    mock_user = _make_mock_user(
        email="expired@example.com",
        password_changed_at=password_changed_at,
    )

    # AUTHORIZE hook passes
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )

    # verify_credential returns user with expired password
    mock_auth_repository.verify_credential.return_value = CredentialVerificationResult(
        user=mock_user,
        active_sessions=[],
    )

    # get_current_time returns "now" so password age check triggers
    mock_auth_repository.get_current_time.return_value = datetime.now(tz=UTC)

    with pytest.raises(PasswordExpired):
        await auth_service.authorize(action)


async def test_authorize_with_post_hook_response(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_valkey_session_client: AsyncMock,
) -> None:
    """Test authorization when POST_AUTHORIZE hook returns a stream response."""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    # Setup successful credential verification
    mock_user = _make_mock_user()
    mock_auth_repository.verify_credential.return_value = CredentialVerificationResult(
        user=mock_user,
        active_sessions=[],
    )

    # Mock user row with keypair (needed for _post_check)
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = _make_mock_keypair_row()
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row

    # First hook (AUTHORIZE) passes normally
    # Second hook (POST_AUTHORIZE) returns a stream response
    mock_stream_response = web.StreamResponse()
    mock_hook_plugin_ctx.dispatch.side_effect = [
        HookResult(status=HookResults.PASSED, result=None, reason=None),
        HookResult(status=HookResults.PASSED, result=mock_stream_response, reason=None),
    ]

    result = await auth_service.authorize(action)

    assert result.stream_response == mock_stream_response
    assert result.authorization_result is None


async def test_authorize_with_valkey_cross_check_cleans_stale_sessions(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_valkey_session_client: AsyncMock,
) -> None:
    """Test that stale sessions (missing from Valkey) are invalidated in DB during cross-check."""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
        otp=None,
    )

    mock_user = _make_mock_user()

    # verify_credential returns user with one active session that is stale in Valkey
    stale_session = ActiveSessionInfo(
        session_token="stale_token",
        created_at=datetime.now(tz=UTC) - timedelta(hours=1),
    )
    mock_auth_repository.verify_credential.return_value = CredentialVerificationResult(
        user=mock_user,
        active_sessions=[stale_session],
    )

    # Mock user row with keypair
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = _make_mock_keypair_row()
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row

    # Both hooks pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )

    # Valkey cross-check: stale session is NOT in Valkey
    mock_valkey_session_client.get_login_session.return_value = None

    # create_login_session succeeds (after stale session cleaned up, count < max)
    mock_auth_repository.create_login_session.return_value = LoginSessionCreationResult(
        session_token="new_session_token",
    )

    result = await auth_service.authorize(action)

    # Stale session should have been invalidated in DB
    mock_auth_repository.invalidate_login_session_by_token.assert_awaited_once_with("stale_token")
    assert result.authorization_result is not None
    assert result.authorization_result.session_token == "new_session_token"


async def test_authorize_force_invalidates_existing_sessions(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_valkey_session_client: AsyncMock,
) -> None:
    """Test that force=True invalidates existing live sessions and creates a new one."""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
        otp=None,
        force=True,
    )

    mock_user = _make_mock_user()

    # verify_credential returns user with one active session that IS live in Valkey
    live_session = ActiveSessionInfo(
        session_token="existing_live_token",
        created_at=datetime.now(tz=UTC) - timedelta(hours=1),
    )
    mock_auth_repository.verify_credential.return_value = CredentialVerificationResult(
        user=mock_user,
        active_sessions=[live_session],
    )

    # Mock user row with keypair
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = _make_mock_keypair_row()
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row

    # Both hooks pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )

    # Valkey cross-check: session IS live
    mock_valkey_session_client.get_login_session.return_value = b"session_data"

    # create_login_session succeeds
    mock_auth_repository.create_login_session.return_value = LoginSessionCreationResult(
        session_token="forced_new_token",
    )

    result = await auth_service.authorize(action)

    # create_login_session should have been called with tokens_to_invalidate
    mock_auth_repository.create_login_session.assert_awaited_once()
    call_kwargs = mock_auth_repository.create_login_session.call_args
    assert call_kwargs.kwargs.get("tokens_to_invalidate") == ["existing_live_token"]

    # Old session should be deleted from Valkey
    mock_valkey_session_client.delete_login_session.assert_awaited_once_with("existing_live_token")

    assert result.authorization_result is not None
    assert result.authorization_result.session_token == "forced_new_token"


async def test_create_login_session_uses_max_concurrent_sessions_from_resource_policy(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
) -> None:
    """Regression: max_concurrent_sessions must come from keypair_resource_policy, not hardcoded."""
    mock_auth_repository.create_login_session.return_value = LoginSessionCreationResult(
        session_token="new_token",
    )

    await auth_service._create_login_session(
        action=AuthorizeAction(
            type=AuthTokenType.KEYPAIR,
            domain_name="default",
            email="test@example.com",
            password="password",
            request=MagicMock(),
            stoken=None,
            otp=None,
        ),
        user=_make_mock_user(),
        keypair_row=_make_mock_keypair_row(max_concurrent_sessions=5),
        live_sessions=[],
        auth_config=AuthConfig(
            max_password_age=timedelta(days=90),
            password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            password_hash_rounds=100_000,
            password_hash_salt_size=32,
            login_session_max_age=604800,
        ),
    )

    call_kwargs = mock_auth_repository.create_login_session.call_args.kwargs
    assert call_kwargs["max_concurrent_sessions"] == 5
