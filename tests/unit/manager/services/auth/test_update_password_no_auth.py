from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.plugin.hook import HookResult, HookResults
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import AuthConfig, ManagerConfig
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.auth import AuthorizationFailed
from ai.backend.manager.errors.common import GenericBadRequest, RejectedByHook
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.update_password_no_auth import (
    UpdatePasswordNoAuthAction,
)
from ai.backend.manager.services.auth.service import AuthService


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
    )
    return mock_provider


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: MagicMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
    )


@pytest.mark.asyncio
async def test_update_password_no_auth_successful(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
    mock_hook_plugin_ctx: AsyncMock,
    mocker: Any,
) -> None:
    """Test successfully updating password without auth"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="current_pass",
        new_password="new_secure_password",
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Setup successful credential check
    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": action.email,
        "password": "hashed_current_pass",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    new_timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)  # Fixed timestamp for comparison
    mock_auth_repository.update_user_password_by_uuid.return_value = new_timestamp

    mocker.patch(
        "ai.backend.manager.services.auth.service.compare_to_hashed_password", return_value=False
    )
    result = await auth_service.update_password_no_auth(action)

    assert result.user_id == UUID("12345678-1234-5678-1234-567812345678")
    assert result.password_changed_at == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_update_password_no_auth_fails_when_max_password_age_is_none(
    mock_hook_plugin_ctx: AsyncMock,
    mock_config_provider: MagicMock,
    auth_service: AuthService,
) -> None:
    """Test update password fails when max_password_age is None"""
    # Set max_password_age to None in the mock
    mock_config_provider.config.auth.max_password_age = None

    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="pass",
        new_password="newpass",
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
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    auth_service: AuthService,
) -> None:
    """Test update password fails with incorrect current password"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="wrong_password",
        new_password="new_password",
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Invalid current password - raises AuthorizationFailed
    mock_auth_repository.check_credential_without_migration.side_effect = AuthorizationFailed(
        "User credential mismatch."
    )

    with pytest.raises(AuthorizationFailed):
        await auth_service.update_password_no_auth(action)


@pytest.mark.asyncio
async def test_update_password_no_auth_fails_when_new_password_same_as_current(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mocker: Any,
    auth_service: AuthService,
) -> None:
    """Test update password fails when new password is same as current"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="same_password",
        new_password="same_password",
        request=MagicMock(),
    )

    # Setup hook to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    # Setup credential check for same password
    mock_auth_repository.check_credential_without_migration.return_value = {
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
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mocker: Any,
    auth_service: AuthService,
) -> None:
    """Test that password update uses retry mechanism"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="retry@example.com",
        current_password="current",
        new_password="new_password",
        request=MagicMock(),
    )

    mock_auth_repository.check_credential_without_migration.return_value = {
        "uuid": UUID("12345678-1234-5678-1234-567812345678"),
        "email": action.email,
        "password": "hashed_current",
        "role": UserRole.USER,
        "status": UserStatus.ACTIVE,
    }

    changed_at = datetime.now(tz=UTC)
    mock_auth_repository.update_user_password_by_uuid.return_value = changed_at

    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=None,
        reason=None,
    )

    mocker.patch(
        "ai.backend.manager.services.auth.service.compare_to_hashed_password", return_value=False
    )
    # execute_with_retry doesn't exist in the service anymore
    result = await auth_service.update_password_no_auth(action)

    assert result.user_id == UUID("12345678-1234-5678-1234-567812345678")
    assert result.password_changed_at == changed_at


@pytest.mark.asyncio
async def test_update_password_no_auth_hook_rejection(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mocker: Any,
    auth_service: AuthService,
) -> None:
    """Test password update fails when hook rejects"""
    action = UpdatePasswordNoAuthAction(
        domain_name="default",
        email="user@example.com",
        current_password="current",
        new_password="weak",
        request=MagicMock(),
    )

    mock_auth_repository.check_credential_without_migration.return_value = {
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
