import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserData
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.auth.types import DelegationTargetUser
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.auth.actions.resolve_access_key_scope import (
    PublicResolveAccessKeyScopeAction,
)
from ai.backend.manager.services.auth.actions.resolve_user_scope import (
    PublicResolveUserScopeAction,
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
    mock_user_repository: AsyncMock,
    mock_group_repository: AsyncMock,
    mock_client_ip_masking_repository: AsyncMock,
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
        client_ip_masking_repository=mock_client_ip_masking_repository,
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


REQUESTER_AK = "AKIAIOSFODNN7EXAMPLE"
OWNER_AK = "AKIAI44QH8DHBEXAMPLE"
REQUESTER_UUID = UserID(uuid.UUID("11111111-1111-1111-1111-111111111111"))
OWNER_UUID = UserID(uuid.UUID("22222222-2222-2222-2222-222222222222"))
DOMAIN_ID = DomainID(uuid.UUID("33333333-3333-3333-3333-333333333333"))


def acting_user(role: UserRole, domain: str = "default") -> UserData:
    return UserData(
        user_id=REQUESTER_UUID,
        is_authorized=True,
        is_admin=role in (UserRole.ADMIN, UserRole.SUPERADMIN),
        is_superadmin=role == UserRole.SUPERADMIN,
        role=role,
        domain_name=domain,
        domain_id=DOMAIN_ID,
    )


@pytest.fixture
def default_keypair(mock_auth_repository: AsyncMock) -> None:
    mock_auth_repository.default_keypair.return_value = SimpleNamespace(access_key=REQUESTER_AK)


class TestResolveAccessKeyScope:
    async def test_owner_none_returns_default_keypair(
        self,
        auth_service: AuthService,
        default_keypair: None,
    ) -> None:
        action = PublicResolveAccessKeyScopeAction(owner_access_key=None)
        with with_user(acting_user(UserRole.USER)):
            result = await auth_service.resolve_access_key_scope(action)
        assert result.requester_access_key == AccessKey(REQUESTER_AK)
        assert result.owner_access_key == AccessKey(REQUESTER_AK)
        assert result.entity_id() == REQUESTER_UUID

    async def test_owner_equals_requester_returns_same_key(
        self,
        auth_service: AuthService,
        default_keypair: None,
    ) -> None:
        action = PublicResolveAccessKeyScopeAction(owner_access_key=REQUESTER_AK)
        with with_user(acting_user(UserRole.ADMIN)):
            result = await auth_service.resolve_access_key_scope(action)
        assert result.owner_access_key == AccessKey(REQUESTER_AK)
        assert result.entity_id() == REQUESTER_UUID

    async def test_regular_user_delegation_raises_forbidden(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        default_keypair: None,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_access_key.return_value = (
            DelegationTargetUser(user_id=OWNER_UUID, role=UserRole.ADMIN, domain_name="default")
        )
        action = PublicResolveAccessKeyScopeAction(owner_access_key=OWNER_AK)
        with with_user(acting_user(UserRole.USER)):
            with pytest.raises(GenericForbidden):
                await auth_service.resolve_access_key_scope(action)

    async def test_nonexistent_owner_access_key_raises_invalid_params(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        default_keypair: None,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_access_key.side_effect = ValueError(
            "Unknown owner access key"
        )
        action = PublicResolveAccessKeyScopeAction(owner_access_key="NONEXISTENT_KEY")
        with with_user(acting_user(UserRole.SUPERADMIN)):
            with pytest.raises(InvalidAPIParameters):
                await auth_service.resolve_access_key_scope(action)

    async def test_cross_domain_admin_raises_forbidden(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        default_keypair: None,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_access_key.return_value = (
            DelegationTargetUser(user_id=OWNER_UUID, role=UserRole.USER, domain_name="other-domain")
        )
        action = PublicResolveAccessKeyScopeAction(owner_access_key=OWNER_AK)
        with with_user(acting_user(UserRole.ADMIN)):
            with pytest.raises(GenericForbidden):
                await auth_service.resolve_access_key_scope(action)

    async def test_delegation_is_judged_on_the_acting_user(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
        default_keypair: None,
    ) -> None:
        """A super admin acting as a regular user (BEP-1058) may not delegate."""
        mock_auth_repository.get_delegation_target_by_access_key.return_value = (
            DelegationTargetUser(user_id=OWNER_UUID, role=UserRole.USER, domain_name="default")
        )
        action = PublicResolveAccessKeyScopeAction(owner_access_key=OWNER_AK)
        with with_user(acting_user(UserRole.USER)):
            with pytest.raises(GenericForbidden):
                await auth_service.resolve_access_key_scope(action)


class TestResolveUserScope:
    async def test_owner_email_none_returns_acting_user(
        self,
        auth_service: AuthService,
    ) -> None:
        action = PublicResolveUserScopeAction(owner_user_email=None)
        with with_user(acting_user(UserRole.USER)):
            result = await auth_service.resolve_user_scope(action)
        assert result.owner_uuid == REQUESTER_UUID
        assert result.owner_role == UserRole.USER
        assert result.entity_id() == REQUESTER_UUID

    async def test_non_superadmin_specifying_email_raises_invalid_params(
        self,
        auth_service: AuthService,
    ) -> None:
        action = PublicResolveUserScopeAction(owner_user_email="other@example.com")
        with with_user(acting_user(UserRole.ADMIN)):
            with pytest.raises(InvalidAPIParameters):
                await auth_service.resolve_user_scope(action)

    async def test_superadmin_delegation_succeeds(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_email.return_value = DelegationTargetUser(
            user_id=OWNER_UUID, role=UserRole.USER, domain_name="default"
        )
        action = PublicResolveUserScopeAction(owner_user_email="owner@example.com")
        with with_user(acting_user(UserRole.SUPERADMIN)):
            result = await auth_service.resolve_user_scope(action)
        assert result.owner_uuid == OWNER_UUID
        assert result.owner_role == UserRole.USER
        assert result.entity_id() == OWNER_UUID

    async def test_nonexistent_email_raises_invalid_params(
        self,
        auth_service: AuthService,
        mock_auth_repository: AsyncMock,
    ) -> None:
        mock_auth_repository.get_delegation_target_by_email.side_effect = ValueError(
            "Unknown user email"
        )
        action = PublicResolveUserScopeAction(owner_user_email="nonexistent@example.com")
        with with_user(acting_user(UserRole.SUPERADMIN)):
            with pytest.raises(InvalidAPIParameters):
                await auth_service.resolve_user_scope(action)
