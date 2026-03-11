from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.user import (
    CreateUserResponse,
    GetUserResponse,
    PurgeUserRequest,
    PurgeUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserRole,
    UserStatus,
)

from .conftest import UserFactory


class TestUserModify:
    async def test_admin_modifies_basic_info(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-1: Admin modifies full_name and description; unchanged fields preserved."""
        unique = secrets.token_hex(4)
        result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(
                full_name=f"Updated Name {unique}",
                description=f"Updated description {unique}",
            ),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.full_name == f"Updated Name {unique}"
        assert result.user.description == f"Updated description {unique}"
        # unchanged fields preserved
        assert result.user.email == target_user.user.email
        assert result.user.status == target_user.user.status

    async def test_admin_changes_username(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-2: Admin changes username; DB updated."""
        unique = secrets.token_hex(4)
        new_username = f"renamed-{unique}"
        result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(username=new_username),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.username == new_username

        get_result = await admin_registry.user.get(target_user.user.id)
        assert isinstance(get_result, GetUserResponse)
        assert get_result.user.username == new_username

    async def test_admin_changes_role(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-3: Admin changes role USER → ADMIN."""
        r = await user_factory(role=UserRole.USER)
        result = await admin_registry.user.update(
            r.user.id,
            UpdateUserRequest(role=UserRole.ADMIN),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.role == UserRole.ADMIN

    async def test_admin_changes_status(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-4: Admin changes status ACTIVE → INACTIVE."""
        r = await user_factory(status=UserStatus.ACTIVE)
        result = await admin_registry.user.update(
            r.user.id,
            UpdateUserRequest(status=UserStatus.INACTIVE),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.status == UserStatus.INACTIVE

    async def test_admin_changes_password(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-5: Admin changes password; HTTP 200."""
        result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(password="new-secure-password-5678"),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.id == target_user.user.id

    async def test_admin_sets_need_password_change(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-6: Admin sets need_password_change flag to True."""
        result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(need_password_change=True),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.need_password_change is True

    async def test_admin_toggles_totp_activated(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-7: Admin toggles totp_activated."""
        original = target_user.user.totp_activated or False
        result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(totp_activated=not original),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.totp_activated == (not original)

    async def test_admin_changes_sudo_session_enabled(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """S-8: Admin changes sudo_session_enabled."""
        original = target_user.user.sudo_session_enabled
        result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(sudo_session_enabled=not original),
        )
        assert isinstance(result, UpdateUserResponse)
        assert result.user.sudo_session_enabled == (not original)

    async def test_modify_nonexistent_user_raises_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Modify non-existent user → NotFoundError (HTTP 404)."""
        with pytest.raises(NotFoundError):
            await admin_registry.user.update(
                uuid.uuid4(),
                UpdateUserRequest(full_name="Ghost"),
            )

    async def test_regular_user_cannot_modify_another_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """F-AUTH-1: Regular user cannot modify another user → PermissionDeniedError (HTTP 403)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.update(
                target_user.user.id,
                UpdateUserRequest(full_name="Denied"),
            )


class TestUserPurge:
    async def test_admin_purges_user_with_no_active_resources(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """S-1: Admin purges user with no active resources → success=True, re-get returns NotFoundError."""
        r = await user_factory()
        purge_result = await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))
        assert isinstance(purge_result, PurgeUserResponse)
        assert purge_result.success is True
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(r.user.id)

    async def test_purge_nonexistent_user_raises_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-2: Purge non-existent user → NotFoundError (HTTP 404)."""
        with pytest.raises(NotFoundError):
            await admin_registry.user.purge(PurgeUserRequest(user_id=uuid.uuid4()))

    async def test_regular_user_cannot_purge(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        """F-AUTH-1: Regular user cannot purge → PermissionDeniedError (HTTP 403)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.purge(PurgeUserRequest(user_id=target_user.user.id))
