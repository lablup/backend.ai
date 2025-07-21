from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.plugin.hook import HookPluginContext, HookResult, HookResults
from ai.backend.manager.config.unified import AuthConfig
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.common import GenericBadRequest, RejectedByHook
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthAction,
)
from ai.backend.manager.services.auth.service import AuthService


@pytest.fixture
def mock_hook_plugin_ctx():
    return MagicMock(spec=HookPluginContext)


@pytest.fixture
def mock_auth_repository():
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(mock_hook_plugin_ctx, mock_auth_repository):
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
    )


@pytest.mark.asyncio
async def test_update_password_no_auth_successful(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mocker,
):
    """Test successfully updating password without auth"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="current_pass",
        new_password="new_secure_password",
        auth_config=AuthConfig(
            max_password_age=timedelta(days=90),
        ),
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Setup successful credential check
    mock_auth_repository.check_credential_validated.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": action.email,
        "password": "hashed_current_pass",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    new_timestamp = datetime(2024, 1, 1, 12, 0, 0)  # Fixed timestamp for comparison
    mock_auth_repository.update_user_password_by_uuid_validated.return_value = new_timestamp

    mocker.patch(
        "ai.backend.manager.services.auth.service.compare_to_hashed_password", return_value=False
    )
    result = await auth_service.update_password_no_auth(action)

    assert result.user_id == UUID("12345678-1234-5678-1234-567812345678")
    assert result.password_changed_at == datetime(2024, 1, 1, 12, 0, 0)


@pytest.mark.asyncio
async def test_update_password_no_auth_fails_when_auth_config_is_none(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
):
    """Test update password fails when auth config is None"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="pass",
        new_password="newpass",
        auth_config=None,
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    with pytest.raises(GenericBadRequest):
        await auth_service.update_password_no_auth(action)


@pytest.mark.asyncio
async def test_update_password_no_auth_fails_when_max_password_age_is_none(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
):
    """Test update password fails when max_password_age is None"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="pass",
        new_password="newpass",
        auth_config=AuthConfig(
            max_password_age=None,
        ),
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    with pytest.raises(GenericBadRequest):
        await auth_service.update_password_no_auth(action)


@pytest.mark.asyncio
async def test_update_password_no_auth_fails_with_incorrect_current_password(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test update password fails with incorrect current password"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="wrong_password",
        new_password="new_password",
        auth_config=AuthConfig(
            max_password_age=timedelta(days=90),
        ),
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Invalid current password
    mock_auth_repository.check_credential_validated.return_value = None

    with pytest.raises(AuthorizationFailed):
        await auth_service.update_password_no_auth(action)


@pytest.mark.asyncio
async def test_update_password_no_auth_fails_when_new_password_same_as_current(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mocker,
):
    """Test update password fails when new password is same as current"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="same_password",
        new_password="same_password",
        auth_config=AuthConfig(
            max_password_age=timedelta(days=90),
        ),
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Setup credential check for same password
    mock_auth_repository.check_credential_validated.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": action.email,
        "password": "hashed_same_password",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    mocker.patch(
        "ai.backend.manager.services.auth.service.compare_to_hashed_password", return_value=True
    )  # New password is same as current
    with pytest.raises(AuthorizationFailed):
        await auth_service.update_password_no_auth(action)


@pytest.mark.asyncio
async def test_update_password_no_auth_with_retry(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mocker,
):
    """Test that password update uses retry mechanism"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="retry@example.com",
        current_password="current",
        new_password="new_password",
        auth_config=AuthConfig(
            max_password_age=timedelta(days=90),
        ),
        request=MagicMock(),
    )

    mock_auth_repository.check_credential_validated.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": action.email,
        "password": "hashed_current",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    changed_at = datetime.now()
    mock_auth_repository.update_user_password_by_uuid_validated.return_value = changed_at

    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    mocker.patch(
        "ai.backend.manager.services.auth.service.compare_to_hashed_password", return_value=False
    )
    mocker.patch(
        "ai.backend.manager.services.auth.service.execute_with_retry", return_value=changed_at
    )
    result = await auth_service.update_password_no_auth(action)

    assert result.user_id == UUID("12345678-1234-5678-1234-567812345678")
    assert result.password_changed_at == changed_at


@pytest.mark.asyncio
async def test_update_password_no_auth_hook_rejection(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mocker,
):
    """Test password update fails when hook rejects"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="current",
        new_password="weak",
        auth_config=AuthConfig(
            max_password_age=timedelta(days=90),
        ),
        request=MagicMock(),
    )

    mock_auth_repository.check_credential_validated.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": action.email,
        "password": "hashed_current",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    # Hook rejects the password
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.REJECTED,
        result=None,
        reason="Password must be at least 8 characters",
    )

    mocker.patch(
        "ai.backend.manager.services.auth.service.compare_to_hashed_password", return_value=False
    )
    with pytest.raises(RejectedByHook) as exc_info:
        await auth_service.update_password_no_auth(action)

    assert "Password must be at least 8 characters" in str(exc_info.value)
