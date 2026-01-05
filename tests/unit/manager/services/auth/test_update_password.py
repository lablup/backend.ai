from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.plugin.hook import HookResult, HookResults
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.common import RejectedByHook
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.update_password import (
    UpdatePasswordAction,
)
from ai.backend.manager.services.auth.service import AuthService


@pytest.fixture
def mock_auth_repository():
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(mock_hook_plugin_ctx, mock_auth_repository, mock_config_provider):
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
    )


@pytest.mark.asyncio
async def test_update_password_successful(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test successful password update"""
    action = UpdatePasswordAction(
        request=MagicMock(),
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        old_password="old_password",
        new_password="new_secure_password",
        new_password_confirm="new_secure_password",
    )

    # Setup hook to pass password format verification
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Valid old password
    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "email": action.email,
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    # Password update succeeds
    mock_auth_repository.update_user_password.return_value = None

    result = await auth_service.update_password(action)

    assert result.success is True
    assert result.message == "Password updated successfully"
    mock_auth_repository.check_credential_without_migration.assert_called_once()
    mock_auth_repository.update_user_password.assert_called_once()


@pytest.mark.asyncio
async def test_update_password_fails_when_new_passwords_dont_match(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test password update fails when new passwords don't match"""
    action = UpdatePasswordAction(
        request=MagicMock(),
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        old_password="old_password",
        new_password="new_password1",
        new_password_confirm="new_password2",
    )

    # Setup hook to pass password format verification
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Valid old password
    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": "12345678-1234-5678-1234-567812345678",
        "email": action.email,
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    result = await auth_service.update_password(action)

    assert result.success is False
    assert result.message == "new password mismatch"
    # When passwords don't match, we return early without checking old password
    mock_auth_repository.check_credential_without_migration.assert_not_called()
    # Password update should not be called when passwords don't match
    mock_auth_repository.update_user_password.assert_not_called()


@pytest.mark.asyncio
async def test_update_password_fails_with_incorrect_old_password(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test password update fails with incorrect old password"""
    action = UpdatePasswordAction(
        request=MagicMock(),
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        old_password="wrong_old_password",
        new_password="new_password",
        new_password_confirm="new_password",
    )

    # Setup hook to pass password format verification
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Invalid old password - raises AuthorizationFailed
    mock_auth_repository.check_credential_without_migration.side_effect = AuthorizationFailed(
        "User credential mismatch."
    )

    with pytest.raises(AuthorizationFailed):
        await auth_service.update_password(action)

    mock_auth_repository.check_credential_without_migration.assert_called_once()
    # Password update should not be called when credential check fails
    mock_auth_repository.update_user_password.assert_not_called()


@pytest.mark.asyncio
async def test_update_password_with_hook_rejection(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test password update fails when hook rejects password format"""
    action = UpdatePasswordAction(
        request=MagicMock(),
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        old_password="correct_old_password",
        new_password="weak",
        new_password_confirm="weak",
    )

    # Valid old password
    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": "test-uuid",
        "email": action.email,
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    # Hook rejects the new password format
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.REJECTED,
        result=None,
        reason="Password is too weak",
    )

    with pytest.raises(RejectedByHook) as exc_info:
        await auth_service.update_password(action)

    assert "Password is too weak" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_password_repository_call(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
    """Test that password update calls repository with correct parameters"""
    action = UpdatePasswordAction(
        request=MagicMock(),
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="test-domain",
        email="update@example.com",
        old_password="old_pass",
        new_password="new_pass123",
        new_password_confirm="new_pass123",
    )

    # Setup successful scenario
    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": "test-uuid",
        "email": action.email,
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    result = await auth_service.update_password(action)

    # Verify repository calls
    mock_auth_repository.check_credential_without_migration.assert_called_once_with(
        "test-domain",
        "update@example.com",
        "old_pass",
    )
    # Verify password was updated with PasswordInfo
    call_args = mock_auth_repository.update_user_password.call_args
    assert call_args[0][0] == "update@example.com"
    password_info = call_args[0][1]
    assert password_info.password == "new_pass123"
    assert password_info.algorithm is not None  # Should be set from config

    # Verify hook was called
    mock_hook_plugin_ctx.dispatch.assert_called_once()
    hook_call = mock_hook_plugin_ctx.dispatch.call_args
    assert hook_call[0][0] == "VERIFY_PASSWORD_FORMAT"

    assert result.success is True
    assert result.message == "Password updated successfully"
