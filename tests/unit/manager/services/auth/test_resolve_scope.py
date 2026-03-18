import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    ResolveAccessKeyScopeAction,
)
from ai.backend.manager.services.auth.actions.resolve_user_scope import (
    ResolveUserScopeAction,
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


REQUESTER_AK = "AKIAIOSFODNN7EXAMPLE"
OWNER_AK = "AKIAI44QH8DHBEXAMPLE"
REQUESTER_UUID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OWNER_UUID = uuid.UUID("22222222-2222-2222-2222-222222222222")


class TestResolveAccessKeyScope:
    async def test_owner_none_returns_requester_key(
        self,
        auth_service: AuthService,
    ) -> None:
        action = ResolveAccessKeyScopeAction(
            requester_access_key=REQUESTER_AK,
            requester_role=UserRole.USER,
            requester_domain="default",
            owner_access_key=None,
        )
        result = await auth_service.resolve_access_key_scope(action)
        assert result.requester_access_key == AccessKey(REQUESTER_AK)
        assert result.owner_access_key == AccessKey(REQUESTER_AK)

    async def test_owner_equals_requester_returns_same_key(
        self,
        auth_service: AuthService,
    ) -> None:
        action = ResolveAccessKeyScopeAction(
            requester_access_key=REQUESTER_AK,
            requester_role=UserRole.ADMIN,
            requester_domain="default",
            owner_access_key=REQUESTER_AK,
        )
        result = await auth_service.resolve_access_key_scope(action)
        assert result.owner_access_key == AccessKey(REQUESTER_AK)

    async def test_regular_user_delegation_raises_forbidden(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_access_key.return_value = (
            "default",
            UserRole.ADMIN,
        )
        action = ResolveAccessKeyScopeAction(
            requester_access_key=REQUESTER_AK,
            requester_role=UserRole.USER,
            requester_domain="default",
            owner_access_key=OWNER_AK,
        )
        with pytest.raises(GenericForbidden):
            await auth_service.resolve_access_key_scope(action)

    async def test_nonexistent_owner_access_key_raises_invalid_params(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_access_key.side_effect = ValueError(
            "Unknown owner access key"
        )
        action = ResolveAccessKeyScopeAction(
            requester_access_key=REQUESTER_AK,
            requester_role=UserRole.SUPERADMIN,
            requester_domain="default",
            owner_access_key="NONEXISTENT_KEY",
        )
        with pytest.raises(InvalidAPIParameters):
            await auth_service.resolve_access_key_scope(action)

    async def test_cross_domain_admin_raises_forbidden(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_access_key.return_value = (
            "other-domain",
            UserRole.USER,
        )
        action = ResolveAccessKeyScopeAction(
            requester_access_key=REQUESTER_AK,
            requester_role=UserRole.ADMIN,
            requester_domain="default",
            owner_access_key=OWNER_AK,
        )
        with pytest.raises(GenericForbidden):
            await auth_service.resolve_access_key_scope(action)


class TestResolveUserScope:
    async def test_owner_email_none_returns_requester(
        self,
        auth_service: AuthService,
    ) -> None:
        action = ResolveUserScopeAction(
            requester_uuid=REQUESTER_UUID,
            requester_role=UserRole.USER,
            requester_domain="default",
            is_superadmin=False,
            owner_user_email=None,
        )
        result = await auth_service.resolve_user_scope(action)
        assert result.owner_uuid == REQUESTER_UUID
        assert result.owner_role == UserRole.USER

    async def test_non_superadmin_specifying_email_raises_invalid_params(
        self,
        auth_service: AuthService,
    ) -> None:
        action = ResolveUserScopeAction(
            requester_uuid=REQUESTER_UUID,
            requester_role=UserRole.ADMIN,
            requester_domain="default",
            is_superadmin=False,
            owner_user_email="other@example.com",
        )
        with pytest.raises(InvalidAPIParameters):
            await auth_service.resolve_user_scope(action)

    async def test_superadmin_delegation_succeeds(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_email.return_value = (
            OWNER_UUID,
            UserRole.USER,
            "default",
        )
        action = ResolveUserScopeAction(
            requester_uuid=REQUESTER_UUID,
            requester_role=UserRole.SUPERADMIN,
            requester_domain="default",
            is_superadmin=True,
            owner_user_email="owner@example.com",
        )
        result = await auth_service.resolve_user_scope(action)
        assert result.owner_uuid == OWNER_UUID
        assert result.owner_role == UserRole.USER

    async def test_nonexistent_email_raises_invalid_params(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_email.side_effect = ValueError(
            "Unknown user email"
        )
        action = ResolveUserScopeAction(
            requester_uuid=REQUESTER_UUID,
            requester_role=UserRole.SUPERADMIN,
            requester_domain="default",
            is_superadmin=True,
            owner_user_email="nonexistent@example.com",
        )
        with pytest.raises(InvalidAPIParameters):
            await auth_service.resolve_user_scope(action)
