from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    GetUserResponse,
    OrderDirection,
    PurgeUserRequest,
    PurgeUserResponse,
    SearchUsersRequest,
    SearchUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserFilter,
    UserOrder,
    UserOrderField,
    UserRole,
    UserStatus,
)

from .conftest import UserFactory


class TestUserCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_factory(
            email=f"new-{unique}@test.local",
            username=f"new-{unique}",
        )
        assert isinstance(result, CreateUserResponse)
        assert result.user.email == f"new-{unique}@test.local"
        assert result.user.username == f"new-{unique}"
        assert result.user.status == UserStatus.ACTIVE
        assert result.user.id is not None

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_user(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        request = CreateUserRequest(
            email=f"denied-{unique}@test.local",
            username=f"denied-{unique}",
            password="test-password-1234",
            domain_name=domain_fixture,
            resource_policy=resource_policy_fixture,
        )
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.create(request)

    @pytest.mark.asyncio
    async def test_create_user_with_optional_fields(
        self,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_factory(
            email=f"opts-{unique}@test.local",
            username=f"opts-{unique}",
            full_name="Full Name Test",
            description="A test user with optional fields",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        assert result.user.full_name == "Full Name Test"
        assert result.user.description == "A test user with optional fields"
        assert result.user.role == UserRole.USER


class TestUserGet:
    @pytest.mark.asyncio
    async def test_admin_gets_user_by_uuid(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        get_result = await admin_registry.user.get(target_user.user.id)
        assert isinstance(get_result, GetUserResponse)
        assert get_result.user.id == target_user.user.id
        assert get_result.user.email == target_user.user.email
        assert get_result.user.username == target_user.user.username

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.get(target_user.user.id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(uuid.uuid4())


class TestUserSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_users(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        await user_factory()
        await user_factory()
        result = await admin_registry.user.search(SearchUsersRequest())
        assert isinstance(result, SearchUsersResponse)
        assert result.pagination.total >= 2
        assert len(result.items) >= 2

    @pytest.mark.asyncio
    async def test_search_with_email_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"emailf-{unique}"
        await user_factory(email=f"{marker}@test.local", username=marker)
        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(email=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total == 1
        assert result.items[0].email == f"{marker}@test.local"

    @pytest.mark.asyncio
    async def test_search_with_status_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await user_factory(
            email=f"statf-{unique}@test.local",
            username=f"statf-{unique}",
            status=UserStatus.INACTIVE,
        )
        result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(
                    email=StringFilter(contains=f"statf-{unique}"),
                ),
            )
        )
        assert result.pagination.total >= 1
        found = [u for u in result.items if u.id == r.user.id]
        assert len(found) == 1
        assert found[0].status == UserStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_search_with_ordering(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        await user_factory(email=f"aaa-{unique1}@test.local", username=f"aaa-{unique1}")
        await user_factory(email=f"zzz-{unique2}@test.local", username=f"zzz-{unique2}")
        result = await admin_registry.user.search(
            SearchUsersRequest(
                order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.DESC)],
            )
        )
        emails = [u.email for u in result.items]
        assert emails == sorted(emails, reverse=True)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.user.search(
            SearchUsersRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.items) <= 1

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_users(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.search(SearchUsersRequest())


class TestUserUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_user_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        update_result = await admin_registry.user.update(
            target_user.user.id,
            UpdateUserRequest(
                username=f"updated-{unique}",
                full_name="Updated Full Name",
                description="Updated description",
            ),
        )
        assert isinstance(update_result, UpdateUserResponse)
        assert update_result.user.username == f"updated-{unique}"
        assert update_result.user.full_name == "Updated Full Name"
        assert update_result.user.description == "Updated description"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.update(
                target_user.user.id,
                UpdateUserRequest(full_name="Denied"),
            )


class TestUserDelete:
    @pytest.mark.asyncio
    async def test_admin_soft_deletes_user(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        delete_result = await admin_registry.user.delete(
            DeleteUserRequest(user_id=target_user.user.id)
        )
        assert isinstance(delete_result, DeleteUserResponse)
        assert delete_result.success is True

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.delete(DeleteUserRequest(user_id=target_user.user.id))


class TestUserPurge:
    @pytest.mark.asyncio
    async def test_admin_purges_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        r = await user_factory()
        purge_result = await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))
        assert isinstance(purge_result, PurgeUserResponse)
        assert purge_result.success is True
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(r.user.id)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_purge_user(
        self,
        user_registry: BackendAIClientRegistry,
        target_user: CreateUserResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.purge(PurgeUserRequest(user_id=target_user.user.id))
