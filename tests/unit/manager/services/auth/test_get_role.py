from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from ai.backend.manager.errors.auth import GroupMembershipNotFoundError
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.get_role import GetRoleAction
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


@pytest.mark.parametrize(
    "description,is_superadmin,is_admin,expected_global,expected_domain",
    [
        ("regular user", False, False, "user", "user"),
        ("superadmin", True, True, "superadmin", "admin"),
        ("domain admin", False, True, "user", "admin"),
    ],
)
@pytest.mark.asyncio
async def test_get_role_simple_cases(
    auth_service: AuthService,
    description: str,
    is_superadmin: bool,
    is_admin: bool,
    expected_global: str,
    expected_domain: str,
):
    """Test role retrieval for simple cases without group logic"""
    action = GetRoleAction(
        user_id=UUID("12345678-1234-5678-1234-567812345678"),
        is_superadmin=is_superadmin,
        is_admin=is_admin,
        group_id=None,
    )

    result = await auth_service.get_role(action)

    assert result.global_role == expected_global
    assert result.domain_role == expected_domain
    assert result.group_role is None


@pytest.mark.asyncio
async def test_get_role_with_valid_group_membership(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
):
    """Test role retrieval for user with valid group membership"""
    group_id = UUID("87654321-4321-8765-4321-876543218765")
    user_id = UUID("12345678-1234-5678-1234-567812345678")

    # Setup valid group membership
    mock_auth_repository.get_group_membership.return_value = {
        "group_id": group_id,
        "user_id": user_id,
    }

    action = GetRoleAction(
        user_id=user_id,
        is_superadmin=False,
        is_admin=False,
        group_id=group_id,
    )

    result = await auth_service.get_role(action)

    assert result.global_role == "user"
    assert result.domain_role == "user"
    assert result.group_role == "user"  # TODO: per-group role is not yet implemented


@pytest.mark.asyncio
async def test_get_role_without_group_membership_raises_error(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
):
    """Test role retrieval fails for user without group membership"""
    invalid_group_id = UUID("99999999-9999-9999-9999-999999999999")
    user_id = UUID("12345678-1234-5678-1234-567812345678")

    # Setup invalid group membership - raises exception
    mock_auth_repository.get_group_membership.side_effect = GroupMembershipNotFoundError(
        "No such project or you are not the member of it."
    )

    action = GetRoleAction(
        user_id=user_id,
        is_superadmin=False,
        is_admin=False,
        group_id=invalid_group_id,
    )

    with pytest.raises(ObjectNotFound):
        await auth_service.get_role(action)


@pytest.mark.asyncio
async def test_get_role_verifies_correct_parameters(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
):
    """Test that get_role passes correct parameters to repository"""
    user_id = UUID("abcdef12-3456-7890-abcd-ef1234567890")
    group_id = UUID("fedcba98-7654-3210-fedc-ba9876543210")

    action = GetRoleAction(
        user_id=user_id,
        is_superadmin=False,
        is_admin=True,
        group_id=group_id,
    )

    mock_auth_repository.get_group_membership.return_value = {
        "group_id": group_id,
        "user_id": user_id,
    }

    result = await auth_service.get_role(action)

    # Verify repository was called with correct parameters
    mock_auth_repository.get_group_membership.assert_called_once_with(group_id, user_id)

    # Verify result
    assert result.global_role == "user"  # Not superadmin
    assert result.domain_role == "admin"  # Is admin
    assert result.group_role == "user"  # Default group role
