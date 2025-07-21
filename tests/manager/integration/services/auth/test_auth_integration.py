"""
Integration tests for auth service with real database.
These tests verify that the service methods work correctly with actual database connections.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.dto.manager.auth.field import AuthTokenType
from ai.backend.common.plugin.hook import HookPluginContext, HookResult, HookResults
from ai.backend.manager.config.unified import AuthConfig
from ai.backend.manager.errors.auth import (
    AuthorizationFailed,
    EmailAlreadyExistsError,
    PasswordExpired,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.authorize import AuthorizeAction
from ai.backend.manager.services.auth.actions.signout import SignoutAction
from ai.backend.manager.services.auth.actions.signup import SignupAction
from ai.backend.manager.services.auth.actions.update_password import UpdatePasswordAction
from ai.backend.manager.services.auth.service import AuthService

# Mark all tests in this module
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
async def mock_hook_plugin_ctx():
    """Mock hook plugin context that passes all hooks"""
    mock_ctx = MagicMock(spec=HookPluginContext)
    mock_ctx.dispatch.return_value = HookResult(
        status=HookResults.PASSED,
        result=[],  # Empty list means no hook handled it, proceed with normal flow
        reason=None,
    )
    mock_ctx.notify.return_value = None
    return mock_ctx


@pytest.fixture
async def auth_repository(database_engine):
    """Real repository instance with database connection"""
    return AuthRepository(db=database_engine)


@pytest.fixture
async def auth_service(mock_hook_plugin_ctx, auth_repository):
    """Service instance with real repository"""
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=auth_repository,
    )


@pytest.mark.asyncio
async def test_signup_and_authorize_flow(auth_service, database_fixture):
    """Test complete signup and authorization flow"""
    # 1. Signup new user
    signup_action = SignupAction(
        domain_name="default",
        email=f"integration_test_{datetime.now().timestamp()}@example.com",
        password="secure_password123",
        username="integration_user",
        full_name="Integration Test User",
        description="User created by integration test",
        request=MagicMock(),
    )

    signup_result = await auth_service.signup(signup_action)

    assert signup_result.user_id is not None
    assert signup_result.access_key is not None
    assert signup_result.secret_key is not None

    # 2. Authorize the newly created user
    auth_action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email=signup_action.email,
        password=signup_action.password,
        request=MagicMock(),
        auth_config=None,
        stoken=None,
    )

    auth_result = await auth_service.authorize(auth_action)

    assert auth_result.authorization_result is not None
    assert auth_result.authorization_result.user_id == signup_result.user_id
    assert auth_result.authorization_result.access_key == signup_result.access_key
    assert auth_result.authorization_result.secret_key == signup_result.secret_key
    assert auth_result.authorization_result.role == UserRole.USER
    assert auth_result.authorization_result.status == UserStatus.ACTIVE


async def test_duplicate_signup_fails(auth_service, database_fixture):
    """Test that duplicate email signup fails"""
    email = f"duplicate_test_{datetime.now().timestamp()}@example.com"

    # First signup
    signup_action = SignupAction(
        domain_name="default",
        email=email,
        password="password123",
        username=None,
        full_name=None,
        description=None,
        request=MagicMock(),
    )

    await auth_service.signup(signup_action)

    # Second signup with same email should fail
    with pytest.raises(EmailAlreadyExistsError):
        await auth_service.signup(signup_action)


async def test_update_password_flow(auth_service, database_fixture, database_engine):
    """Test password update flow"""
    # Create a user first
    email = f"password_test_{datetime.now().timestamp()}@example.com"
    old_password = "old_password123"
    new_password = "new_password456"

    signup_action = SignupAction(
        domain_name="default",
        email=email,
        password=old_password,
        username="password_test_user",
        full_name="Password Test User",
        description=None,
        request=MagicMock(),
    )

    await auth_service.signup(signup_action)

    # Update password
    query = sa.select(UserRow.uuid).where(UserRow.email == email)
    user_id = None
    async with database_engine.connect() as session:
        result = await session.execute(query)
        user_id = result.scalar()
    update_action = UpdatePasswordAction(
        user_id=user_id,
        domain_name="default",
        email=email,
        old_password=old_password,
        new_password=new_password,
        new_password_confirm=new_password,
        request=MagicMock(),
    )

    update_result = await auth_service.update_password(update_action)
    assert update_result.success is True

    # Verify old password no longer works
    auth_action_old = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email=email,
        password=old_password,
        request=MagicMock(),
        auth_config=None,
        stoken=None,
    )

    with pytest.raises(AuthorizationFailed):
        await auth_service.authorize(auth_action_old)

    # Verify new password works
    auth_action_new = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email=email,
        password=new_password,
        request=MagicMock(),
        auth_config=None,
        stoken=None,
    )

    auth_result = await auth_service.authorize(auth_action_new)
    assert auth_result.authorization_result is not None


async def test_signout_flow(auth_service, database_fixture, database_engine):
    """Test signout flow"""
    # Create a user first
    email = f"signout_test_{datetime.now().timestamp()}@example.com"
    password = "password123"

    signup_action = SignupAction(
        domain_name="default",
        email=email,
        password=password,
        username="signout_test_user",
        full_name="Signout Test User",
        description=None,
        request=MagicMock(),
    )

    await auth_service.signup(signup_action)

    # Verify user can authenticate
    auth_action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email=email,
        password=password,
        request=MagicMock(),
        auth_config=None,
        stoken=None,
    )

    auth_result = await auth_service.authorize(auth_action)
    assert auth_result.authorization_result is not None

    # Signout
    user_id = None
    query = sa.select(UserRow.uuid).where(UserRow.email == email)
    async with database_engine.connect() as session:
        result = await session.execute(query)
        user_id = result.scalar()
    signout_action = SignoutAction(
        user_id=user_id,
        domain_name="default",
        email=email,
        password=password,
        requester_email=email,
    )

    signout_result = await auth_service.signout(signout_action)
    assert signout_result.success is True

    # Verify user can no longer authenticate
    with pytest.raises(AuthorizationFailed):
        await auth_service.authorize(auth_action)


async def test_password_expiry_check(auth_service, auth_repository, database_fixture):
    """Test password expiry check during authorization"""
    # Create a user with an old password change date
    email = f"expiry_test_{datetime.now().timestamp()}@example.com"
    password = "password123"

    signup_action = SignupAction(
        domain_name="default",
        email=email,
        password=password,
        username="expiry_test_user",
        full_name="Expiry Test User",
        description=None,
        request=MagicMock(),
    )

    await auth_service.signup(signup_action)

    # Manually update password_changed_at to be old
    old_date = datetime.now() - timedelta(days=100)
    async with auth_repository._db.begin() as conn:
        await conn.execute(
            sa.update(UserRow).where(UserRow.email == email).values(password_changed_at=old_date)
        )

    # Try to authorize with password age check
    auth_config = AuthConfig(
        max_password_age=timedelta(days=90),
    )

    auth_action = AuthorizeAction(
        type=AuthTokenType.KEYPAIR,
        domain_name="default",
        email=email,
        password=password,
        request=MagicMock(),
        auth_config=auth_config,
        stoken=None,
    )

    with pytest.raises(PasswordExpired):
        await auth_service.authorize(auth_action)
