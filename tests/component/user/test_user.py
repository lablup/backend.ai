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


class TestUserCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_user(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        request = CreateUserRequest(
            email=f"new-{unique}@test.local",
            username=f"new-{unique}",
            password="test-password-1234",
            domain_name=domain_fixture,
            resource_policy=resource_policy_fixture,
        )
        result = await admin_registry.user.create(request)
        try:
            assert isinstance(result, CreateUserResponse)
            assert result.user.email == request.email
            assert result.user.username == request.username
            assert result.user.domain_name == domain_fixture
            assert result.user.status == UserStatus.ACTIVE
            assert result.user.id is not None
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=result.user.id))

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_user(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        request = CreateUserRequest(
            email="denied@test.local",
            username="denied",
            password="test-password-1234",
            domain_name=domain_fixture,
            resource_policy=resource_policy_fixture,
        )
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.create(request)

    @pytest.mark.asyncio
    async def test_create_user_with_optional_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        request = CreateUserRequest(
            email=f"opts-{unique}@test.local",
            username=f"opts-{unique}",
            password="test-password-1234",
            domain_name=domain_fixture,
            resource_policy=resource_policy_fixture,
            full_name="Full Name Test",
            description="A test user with optional fields",
            status=UserStatus.ACTIVE,
            role=UserRole.USER,
        )
        result = await admin_registry.user.create(request)
        try:
            assert result.user.full_name == "Full Name Test"
            assert result.user.description == "A test user with optional fields"
            assert result.user.role == UserRole.USER
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=result.user.id))


class TestUserGet:
    @pytest.mark.asyncio
    async def test_admin_gets_user_by_uuid(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        create_result = await admin_registry.user.create(
            CreateUserRequest(
                email=f"get-{unique}@test.local",
                username=f"get-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            get_result = await admin_registry.user.get(create_result.user.id)
            assert isinstance(get_result, GetUserResponse)
            assert get_result.user.id == create_result.user.id
            assert get_result.user.email == create_result.user.email
            assert get_result.user.username == create_result.user.username
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=create_result.user.id))

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        create_result = await admin_registry.user.create(
            CreateUserRequest(
                email=f"getdeny-{unique}@test.local",
                username=f"getdeny-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            with pytest.raises(PermissionDeniedError):
                await user_registry.user.get(create_result.user.id)
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=create_result.user.id))

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
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        r1 = await admin_registry.user.create(
            CreateUserRequest(
                email=f"search1-{unique1}@test.local",
                username=f"search1-{unique1}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        r2 = await admin_registry.user.create(
            CreateUserRequest(
                email=f"search2-{unique2}@test.local",
                username=f"search2-{unique2}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            result = await admin_registry.user.search(SearchUsersRequest())
            assert isinstance(result, SearchUsersResponse)
            assert result.pagination.total >= 2
            assert len(result.items) >= 2
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r1.user.id))
            await admin_registry.user.purge(PurgeUserRequest(user_id=r2.user.id))

    @pytest.mark.asyncio
    async def test_search_with_email_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"emailf-{unique}"
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"{marker}@test.local",
                username=marker,
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            result = await admin_registry.user.search(
                SearchUsersRequest(
                    filter=UserFilter(email=StringFilter(contains=marker)),
                )
            )
            assert result.pagination.total == 1
            assert result.items[0].email == f"{marker}@test.local"
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))

    @pytest.mark.asyncio
    async def test_search_with_status_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"statf-{unique}@test.local",
                username=f"statf-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
                status=UserStatus.INACTIVE,
            )
        )
        try:
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
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))

    @pytest.mark.asyncio
    async def test_search_with_ordering(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique1 = secrets.token_hex(4)
        unique2 = secrets.token_hex(4)
        r1 = await admin_registry.user.create(
            CreateUserRequest(
                email=f"aaa-{unique1}@test.local",
                username=f"aaa-{unique1}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        r2 = await admin_registry.user.create(
            CreateUserRequest(
                email=f"zzz-{unique2}@test.local",
                username=f"zzz-{unique2}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            result = await admin_registry.user.search(
                SearchUsersRequest(
                    order=[UserOrder(field=UserOrderField.EMAIL, direction=OrderDirection.DESC)],
                )
            )
            emails = [u.email for u in result.items]
            assert emails == sorted(emails, reverse=True)
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r1.user.id))
            await admin_registry.user.purge(PurgeUserRequest(user_id=r2.user.id))

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
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"upd-{unique}@test.local",
                username=f"upd-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            update_result = await admin_registry.user.update(
                r.user.id,
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
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"updeny-{unique}@test.local",
                username=f"updeny-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            with pytest.raises(PermissionDeniedError):
                await user_registry.user.update(
                    r.user.id,
                    UpdateUserRequest(full_name="Denied"),
                )
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))


class TestUserDelete:
    @pytest.mark.asyncio
    async def test_admin_soft_deletes_user(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"del-{unique}@test.local",
                username=f"del-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            delete_result = await admin_registry.user.delete(DeleteUserRequest(user_id=r.user.id))
            assert isinstance(delete_result, DeleteUserResponse)
            assert delete_result.success is True
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"deldeny-{unique}@test.local",
                username=f"deldeny-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            with pytest.raises(PermissionDeniedError):
                await user_registry.user.delete(DeleteUserRequest(user_id=r.user.id))
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))


class TestUserPurge:
    @pytest.mark.asyncio
    async def test_admin_purges_user(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"purge-{unique}@test.local",
                username=f"purge-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        purge_result = await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))
        assert isinstance(purge_result, PurgeUserResponse)
        assert purge_result.success is True
        with pytest.raises(NotFoundError):
            await admin_registry.user.get(r.user.id)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_purge_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        r = await admin_registry.user.create(
            CreateUserRequest(
                email=f"purdeny-{unique}@test.local",
                username=f"purdeny-{unique}",
                password="test-password-1234",
                domain_name=domain_fixture,
                resource_policy=resource_policy_fixture,
            )
        )
        try:
            with pytest.raises(PermissionDeniedError):
                await user_registry.user.purge(PurgeUserRequest(user_id=r.user.id))
        finally:
            await admin_registry.user.purge(PurgeUserRequest(user_id=r.user.id))
