from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.signout import SignoutAction
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
async def test_signout_successful_with_valid_credentials(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
):
    """Test successful signout with valid credentials"""
    action = SignoutAction(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        password="correct_password",
        requester_email="user@example.com",
    )

    # Setup valid credential check
    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": "user@example.com",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }
    mock_auth_repository.deactivate_user_and_keypairs.return_value = None

    result = await auth_service.signout(action)

    assert result.success is True
    mock_auth_repository.check_credential_without_migration.assert_called_once()
    mock_auth_repository.deactivate_user_and_keypairs.assert_called_once()


@pytest.mark.asyncio
async def test_signout_fails_when_not_account_owner(
    auth_service: AuthService,
):
    """Test signout fails when requester is not the account owner"""
    action = SignoutAction(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        password="password",
        requester_email="other@example.com",  # Different from email
    )

    with pytest.raises(GenericForbidden):
        await auth_service.signout(action)


@pytest.mark.asyncio
async def test_signout_fails_with_invalid_credentials(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
):
    """Test signout fails with invalid credentials"""
    action = SignoutAction(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        domain_name="default",
        email="user@example.com",
        password="wrong_password",
        requester_email="user@example.com",
    )

    # Setup invalid credential check - raises AuthorizationFailed for invalid credentials
    mock_auth_repository.check_credential_without_migration.side_effect = AuthorizationFailed(
        "User credential mismatch."
    )

    with pytest.raises(AuthorizationFailed):
        await auth_service.signout(action)

    mock_auth_repository.check_credential_without_migration.assert_called_once()
