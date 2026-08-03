from __future__ import annotations

import random
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.plugin.hook import HookResult, HookResults
from ai.backend.manager.data.auth.types import UserCreationData
from ai.backend.manager.errors.auth import EmailAlreadyExistsError, UserCreationError
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.services.auth.actions.signup import SignupAction
from ai.backend.manager.services.auth.service import AuthService


def make_mock_keypair() -> MagicMock:
    keypair = MagicMock()
    keypair.access_key = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=20))
    keypair.secret_key = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=40))
    return keypair


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: AsyncMock,
    mock_user_repository: AsyncMock,
    mock_group_repository: AsyncMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
        valkey_session_client=AsyncMock(),
        user_resource_policy_repository=AsyncMock(spec=UserResourcePolicyRepository),
        user_repository=mock_user_repository,
        group_repository=mock_group_repository,
        ssh_key_validator=AsyncMock(),
    )


async def test_signup_successful_with_minimal_data(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
    mock_hook_plugin_ctx: AsyncMock,
) -> None:
    """Test successful user signup with minimal data"""
    action = SignupAction(
        domain_name="default",
        email="newuser@example.com",
        password="secure_password123",
        username=None,
        full_name=None,
        description=None,
        request=MagicMock(),
    )

    # Setup hook behavior - both PRE_SIGNUP and VERIFY_PASSWORD_FORMAT pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=[{}],  # Empty dict for hook results
        reason=None,
    )

    # Setup repository behavior
    mock_auth_repository.check_email_exists.return_value = False

    mock_user = MagicMock()
    mock_user.uuid = UUID("12345678-1234-5678-1234-567812345678")
    mock_keypair = make_mock_keypair()
    mock_auth_repository.create_user_with_keypair.return_value = UserCreationData(
        user=mock_user, keypair=mock_keypair
    )

    result = await auth_service.signup(action)

    assert result.user_id == UUID("12345678-1234-5678-1234-567812345678")
    assert result.access_key == mock_keypair.access_key
    assert result.secret_key == mock_keypair.secret_key


async def test_signup_successful_with_full_data(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    auth_service: AuthService,
) -> None:
    """Test successful user signup with full data"""
    action = SignupAction(
        domain_name="custom",
        email="fulluser@example.com",
        password="another_secure_pass",
        username="fulluser",
        full_name="Full User Name",
        description="A test user account",
        request=MagicMock(),
    )

    # Setup hook behavior - both PRE_SIGNUP and VERIFY_PASSWORD_FORMAT pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=[{}],  # Empty dict for hook results
        reason=None,
    )

    # Setup repository behavior
    mock_auth_repository.check_email_exists.return_value = False

    mock_user = MagicMock()
    mock_user.uuid = UUID("87654321-4321-8765-4321-876543218765")
    mock_keypair = make_mock_keypair()
    mock_auth_repository.create_user_with_keypair.return_value = UserCreationData(
        user=mock_user, keypair=mock_keypair
    )

    result = await auth_service.signup(action)

    assert result.user_id == UUID("87654321-4321-8765-4321-876543218765")
    assert result.access_key == mock_keypair.access_key
    assert result.secret_key == mock_keypair.secret_key


async def test_signup_fails_when_email_already_exists(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    auth_service: AuthService,
) -> None:
    """Test signup fails when email already exists"""
    action = SignupAction(
        domain_name="default",
        email="existing@example.com",
        password="password123",
        username=None,
        full_name=None,
        description=None,
        request=MagicMock(),
    )

    # Setup hook behavior - both PRE_SIGNUP and VERIFY_PASSWORD_FORMAT pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=[{}],  # Empty dict for hook results
        reason=None,
    )

    # Setup repository behavior - email already exists
    mock_auth_repository.check_email_exists.return_value = True

    with pytest.raises(EmailAlreadyExistsError):
        await auth_service.signup(action)

    mock_auth_repository.check_email_exists.assert_called_once()


async def test_signup_with_hook_override(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mock_group_repository: AsyncMock,
    auth_service: AuthService,
) -> None:
    """Test signup when PRE_SIGNUP hook overrides user data"""
    action = SignupAction(
        domain_name="default",
        email="hook@example.com",
        password="password123",
        username="hookuser",
        full_name="Hook User",
        description="Original description",
        request=MagicMock(),
    )

    # PRE_SIGNUP hook overrides some user data
    hook_override = {
        "full_name": "Modified by Hook",
        "description": "Hook modified description",
        "status": UserStatus.BEFORE_VERIFICATION,
        "role": UserRole.ADMIN,
        "resource_policy": "premium",
        "group": "special",
    }

    # Setup hook responses
    mock_hook_plugin_ctx.dispatch.side_effect = [
        HookResult(status=HookResults.PASSED, result=[hook_override], reason=None),  # PRE_SIGNUP
        HookResult(status=HookResults.PASSED, result=None, reason=None),  # VERIFY_PASSWORD_FORMAT
    ]

    mock_auth_repository.check_email_exists.return_value = False

    project_id = UUID("22222222-2222-2222-2222-222222222222")
    mock_group_repository.project_id_by_name_in_domain.return_value = project_id

    # Capture the actual call to create_user_with_keypair
    mock_user = MagicMock()
    mock_user.uuid = UUID("11111111-1111-1111-1111-111111111111")
    mock_keypair = make_mock_keypair()
    mock_auth_repository.create_user_with_keypair.return_value = UserCreationData(
        user=mock_user, keypair=mock_keypair
    )

    result = await auth_service.signup(action)

    # Verify the repository was called with modified user/keypair data
    call_args = mock_auth_repository.create_user_with_keypair.call_args
    user_data = call_args.kwargs["user_data"]

    assert user_data["full_name"] == "Modified by Hook"
    assert user_data["description"] == "Hook modified description"
    assert user_data["status"] == UserStatus.BEFORE_VERIFICATION
    assert user_data["role"] == UserRole.ADMIN
    assert call_args.kwargs["keypair_resource_policy"] == "premium"
    assert call_args.kwargs["project_ids"] == [project_id]

    # Verify the hook-overridden ``group`` is forwarded to the project lookup.
    mock_group_repository.project_id_by_name_in_domain.assert_called_once_with(
        action.domain_name, "special"
    )

    assert result.user_id == mock_user.uuid
    assert result.access_key == mock_keypair.access_key


async def test_signup_creation_error(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    auth_service: AuthService,
) -> None:
    """Test signup fails when user creation raises an error"""
    action = SignupAction(
        domain_name="default",
        email="error@example.com",
        password="password123",
        username=None,
        full_name=None,
        description=None,
        request=MagicMock(),
    )

    # Setup hooks to pass
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=[{}],
        reason=None,
    )

    mock_auth_repository.check_email_exists.return_value = False
    mock_auth_repository.create_user_with_keypair.side_effect = UserCreationError("Database error")

    with pytest.raises(InternalServerError) as exc_info:
        await auth_service.signup(action)

    assert "Error creating user account" in str(exc_info.value)


async def test_signup_post_hook_notification(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    auth_service: AuthService,
) -> None:
    """Test that POST_SIGNUP hook is notified after successful signup"""
    request_mock = MagicMock()
    request_mock.headers = {"Accept-Language": "ko-kr,ko;q=0.9,en;q=0.8"}

    action = SignupAction(
        domain_name="default",
        email="notify@example.com",
        password="password123",
        username=None,
        full_name=None,
        description=None,
        request=request_mock,
    )

    # Setup successful signup
    mock_hook_plugin_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=[{}],
        reason=None,
    )
    mock_auth_repository.check_email_exists.return_value = False

    mock_user = MagicMock()
    mock_user.uuid = UUID("99999999-9999-9999-9999-999999999999")
    mock_keypair = make_mock_keypair()
    mock_auth_repository.create_user_with_keypair.return_value = UserCreationData(
        user=mock_user, keypair=mock_keypair
    )

    result = await auth_service.signup(action)

    # Verify POST_SIGNUP notification was called
    mock_hook_plugin_ctx.notify.assert_called_once_with(
        "POST_SIGNUP",
        ("notify@example.com", mock_user.uuid, {"lang": "ko-kr"}),
    )

    assert result.user_id == mock_user.uuid
