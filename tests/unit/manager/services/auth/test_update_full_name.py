from unittest.mock import AsyncMock

import pytest

from ai.backend.common.exception import UserNotFound
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.update_full_name import (
    UpdateFullNameAction,
)
from ai.backend.manager.services.auth.service import AuthService


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: AsyncMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
    )


@pytest.mark.asyncio
async def test_update_full_name_successful(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
) -> None:
    """Test successfully updating full name for existing user"""
    action = UpdateFullNameAction(
        user_id="12345678-1234-5678-1234-567812345678",
        email="user@example.com",
        domain_name="default",
        full_name="New Full Name",
    )

    mock_auth_repository.update_user_full_name.return_value = True

    result = await auth_service.update_full_name(action)
    mock_auth_repository.update_user_full_name.assert_called_once_with(
        action.email,
        action.domain_name,
        action.full_name,
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_update_full_name_fails_for_nonexistent_user() -> None:
    """Test updating full name fails for non-existent user"""
    action = UpdateFullNameAction(
        user_id="12345678-1234-5678-1234-567812345678",
        email="nonexistent@example.com",
        domain_name="default",
        full_name="Some Name",
    )

    mock_auth_repository.update_user_full_name.side_effect = UserNotFound(
        extra_data={"email": action.email, "domain": action.domain_name}
    )

    with pytest.raises(UserNotFound):
        await auth_service.update_full_name(action)

    mock_auth_repository.update_user_full_name.assert_called_once_with(
        action.email,
        action.domain_name,
        action.full_name,
    )


@pytest.mark.asyncio
async def test_update_full_name_repository_call() -> None:
    """Test that update full name calls repository with correct parameters"""
    action = UpdateFullNameAction(
        user_id="12345678-1234-5678-1234-567812345678",
        email="test@example.com",
        domain_name="test-domain",
        full_name="Test User Full Name",
    )

    mock_auth_repository.update_user_full_name.return_value = True

    result = await auth_service.update_full_name(action)

    # Verify repository was called correctly
    mock_auth_repository.update_user_full_name.assert_called_once_with(
        "test@example.com",
        "test-domain",
        "Test User Full Name",
    )
    assert result.success is True
