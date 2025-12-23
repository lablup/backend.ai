from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from aiohttp import web

from ai.backend.common.dto.manager.auth.field import AuthTokenType
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.plugin.hook import HookPluginContext, HookResult, HookResults
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import AuthConfig, ManagerConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.auth import AuthorizationFailed, PasswordExpired
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.authorize import (
    AuthorizeAction,
)
from ai.backend.manager.services.auth.service import AuthService


@pytest.fixture
def mock_hook_plugin_ctx():
    return MagicMock(spec=HookPluginContext)


@pytest.fixture
def mock_auth_repository():
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def mock_config_provider():
    mock_provider = MagicMock(spec=ManagerConfigProvider)
    mock_provider.config = MagicMock(spec=ManagerConfig)
    mock_provider.config.auth = AuthConfig(
        max_password_age=timedelta(days=90),
        password_hash_algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        password_hash_rounds=100_000,
        password_hash_salt_size=32,
    )
    return mock_provider


@pytest.fixture
def auth_service(mock_hook_plugin_ctx, mock_auth_repository, mock_config_provider):
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
    )


@pytest.fixture
def setup_successful_auth(mock_auth_repository, mock_hook_plugin_ctx):
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )
    mock_auth_repository.check_credential_with_migration.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": "test@example.com",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
        "password_changed_at": None,
    }
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = MagicMock(
        access_key="test_access_key",
        secret_key="test_secret_key",
        mapping={"access_key": "test_access_key"},
    )
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row


@pytest.mark.asyncio
async def test_authorize_success(auth_service, setup_successful_auth):
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="correct_password",
        request=MagicMock(),
        stoken=None,
    )

    result = await auth_service.authorize(action)

    assert result.authorization_result is not None
    assert result.authorization_result.access_key == "test_access_key"


@pytest.mark.asyncio
async def test_authorize_invalid_token_type(auth_service, mock_hook_plugin_ctx):
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
    )

    with pytest.raises(InvalidAPIParameters):
        await auth_service.authorize(action)


@pytest.mark.asyncio
async def test_authorize_invalid_credentials(
    auth_service, mock_hook_plugin_ctx, mock_auth_repository
):
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED, result=None, reason=None
    )
    mock_auth_repository.check_credential_with_migration.side_effect = AuthorizationFailed(
        "User credential mismatch."
    )

    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="wrong_password",
        request=MagicMock(),
        stoken=None,
    )

    with pytest.raises(AuthorizationFailed):
        await auth_service.authorize(action)


@pytest.mark.asyncio
async def test_authorize_with_hook_authorization(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test authorization when hook provides the user"""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="hook@example.com",
        password="any_password",
        request=MagicMock(),
        stoken=None,
    )

    # Hook returns user data
    hook_user = {
        "uuid": UUID("87654321-4321-8765-4321-876543218765"),
        "email": "hook@example.com",
        "role": UserRole.ADMIN,
        "status": UserStatus.ACTIVE,
        "password_changed_at": None,
    }
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=hook_user,
        reason=None,
    )

    # Mock user row
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = MagicMock(
        access_key="hook_access_key",
        secret_key="hook_secret_key",
        mapping={"access_key": "hook_access_key"},
    )
    mock_auth_repository.get_user_row_by_uuid.return_value = mock_user_row

    result = await auth_service.authorize(action)

    assert result.authorization_result is not None
    assert result.authorization_result.access_key == "hook_access_key"
    assert result.authorization_result.secret_key == "hook_secret_key"
    assert result.authorization_result.user_id == hook_user["uuid"]
    assert result.authorization_result.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_authorize_with_password_expiry(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: MagicMock,
):
    """Test authorization fails when password is expired"""
    # The mock_config_provider already has max_password_age set to 90 days

    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="expired@example.com",
        password="old_password",
        request=MagicMock(),
        stoken=None,
    )

    # Setup expired password
    password_changed_at = datetime.now() - timedelta(days=100)
    mock_auth_repository.check_credential_with_migration.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": "expired@example.com",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
        "password_changed_at": password_changed_at,
    }
    mock_auth_repository.get_current_time.return_value = datetime.now()

    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    with pytest.raises(PasswordExpired):
        await auth_service.authorize(action)


@pytest.mark.asyncio
async def test_authorize_with_post_hook_response(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test authorization when POST_AUTHORIZE hook returns a stream response"""
    action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email="test@example.com",
        password="password",
        request=MagicMock(),
        stoken=None,
    )

    # Setup successful credential check
    mock_auth_repository.check_credential_with_migration.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": "test@example.com",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
        "password_changed_at": None,
    }

    # Mock user row
    mock_user_row = MagicMock()
    mock_user_row.get_main_keypair_row.return_value = MagicMock(
        access_key="test_access_key",
        secret_key="test_secret_key",
        mapping={"access_key": "test_access_key"},
    )
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
