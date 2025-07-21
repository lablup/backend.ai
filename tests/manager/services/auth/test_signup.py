from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.plugin.hook import HookPluginContext, HookResult, HookResults
from ai.backend.manager.errors.auth import EmailAlreadyExistsError, UserCreationError
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.signup import SignupAction
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
async def test_signup_successful_with_minimal_data(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
    mocker,
):
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
    mock_auth_repository.create_user_with_keypair.return_value = mock_user

    # Mock the generated keypair
    mocker.patch(
        "ai.backend.manager.services.auth.service.generate_keypair",
        return_value=("AKIA1234567890ABCDEF", "abcdef1234567890abcdef1234567890abcdef12"),
    )

    result = await auth_service.signup(action)

    assert result.user_id == UUID("12345678-1234-5678-1234-567812345678")
    assert result.access_key == "AKIA1234567890ABCDEF"
    assert result.secret_key == "abcdef1234567890abcdef1234567890abcdef12"


@pytest.mark.asyncio
async def test_signup_successful_with_full_data(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
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
    mock_auth_repository.create_user_with_keypair.return_value = mock_user

    # Mock the generated keypair
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "ai.backend.manager.services.auth.service.generate_keypair",
            lambda: ("AKIA0987654321FEDCBA", "fedcba0987654321fedcba0987654321fedcba09"),
        )

        result = await auth_service.signup(action)

    assert result.user_id == UUID("87654321-4321-8765-4321-876543218765")
    assert result.access_key == "AKIA0987654321FEDCBA"
    assert result.secret_key == "fedcba0987654321fedcba0987654321fedcba09"


@pytest.mark.asyncio
async def test_signup_fails_when_email_already_exists(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
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


@pytest.mark.asyncio
async def test_signup_with_hook_override(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
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

    # Capture the actual call to create_user_with_keypair
    mock_user = MagicMock()
    mock_user.uuid = UUID("11111111-1111-1111-1111-111111111111")
    mock_auth_repository.create_user_with_keypair.return_value = mock_user

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "ai.backend.manager.services.auth.service.generate_keypair",
            lambda: ("AKIAHOOK12345678", "hooksecret123456789012345678901234567890"),
        )
        result = await auth_service.signup(action)

    # Verify the repository was called with modified data
    call_args = mock_auth_repository.create_user_with_keypair.call_args
    user_data = call_args.kwargs["user_data"]
    keypair_data = call_args.kwargs["keypair_data"]

    assert user_data["full_name"] == "Modified by Hook"
    assert user_data["description"] == "Hook modified description"
    assert user_data["status"] == UserStatus.BEFORE_VERIFICATION
    assert user_data["role"] == UserRole.ADMIN
    assert keypair_data["resource_policy"] == "premium"
    assert call_args.kwargs["group_name"] == "special"

    assert result.user_id == mock_user.uuid
    assert result.access_key == "AKIAHOOK12345678"


@pytest.mark.asyncio
async def test_signup_creation_error(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
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


@pytest.mark.asyncio
async def test_signup_post_hook_notification(
    auth_service: AuthService,
    mock_hook_plugin_ctx: MagicMock,
    mock_auth_repository: AsyncMock,
):
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
    mock_auth_repository.create_user_with_keypair.return_value = mock_user

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "ai.backend.manager.services.auth.service.generate_keypair",
            lambda: ("AKIANOTIFY123456", "notifysecret12345678901234567890abcdef12"),
        )
        result = await auth_service.signup(action)

    # Verify POST_SIGNUP notification was called
    mock_hook_plugin_ctx.notify.assert_called_once_with(
        "POST_SIGNUP",
        ("notify@example.com", mock_user.uuid, {"lang": "ko-kr"}),
    )

    assert result.user_id == mock_user.uuid
