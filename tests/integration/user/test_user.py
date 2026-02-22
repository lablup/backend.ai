from __future__ import annotations

import secrets

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    PurgeUserRequest,
    SearchUsersRequest,
    UpdateUserRequest,
    UserFilter,
    UserStatus,
)

from .conftest import UserFactory


@pytest.mark.integration
class TestUserLifecycle:
    @pytest.mark.asyncio
    async def test_full_user_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """create -> get -> update -> search (verify updated) -> delete -> verify deleted status"""
        unique = secrets.token_hex(4)
        create_result = await user_factory(
            email=f"lifecycle-{unique}@test.local",
            username=f"lifecycle-{unique}",
            full_name="Lifecycle Test User",
        )
        user_id = create_result.user.id
        assert create_result.user.email == f"lifecycle-{unique}@test.local"
        assert create_result.user.status == UserStatus.ACTIVE

        # Get
        get_result = await admin_registry.user.get(user_id)
        assert get_result.user.id == user_id
        assert get_result.user.email == f"lifecycle-{unique}@test.local"

        # Update
        update_result = await admin_registry.user.update(
            user_id,
            UpdateUserRequest(
                full_name="Updated Lifecycle User",
                description="Updated via lifecycle test",
            ),
        )
        assert update_result.user.full_name == "Updated Lifecycle User"
        assert update_result.user.description == "Updated via lifecycle test"

        # Search (verify updated fields)
        search_result = await admin_registry.user.search(
            SearchUsersRequest(
                filter=UserFilter(email=StringFilter(contains=f"lifecycle-{unique}")),
            )
        )
        assert search_result.pagination.total == 1
        assert search_result.items[0].full_name == "Updated Lifecycle User"

        # Delete (soft)
        delete_result = await admin_registry.user.delete(DeleteUserRequest(user_id=user_id))
        assert delete_result.success is True

        # Verify deleted status
        after_delete = await admin_registry.user.get(user_id)
        assert after_delete.user.status == UserStatus.DELETED

    @pytest.mark.asyncio
    async def test_create_and_purge_user(
        self,
        admin_registry: BackendAIClientRegistry,
        user_factory: UserFactory,
    ) -> None:
        """create -> purge -> verify user is gone (get returns 404)"""
        create_result = await user_factory()
        user_id = create_result.user.id

        purge_result = await admin_registry.user.purge(PurgeUserRequest(user_id=user_id))
        assert purge_result.success is True

        with pytest.raises(NotFoundError):
            await admin_registry.user.get(user_id)


@pytest.mark.integration
class TestUserPermissionVerification:
    @pytest.mark.asyncio
    async def test_regular_user_denied_all_admin_endpoints(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
        target_user: CreateUserResponse,
    ) -> None:
        """Systematically test all 6 methods with user_registry."""
        target_id = target_user.user.id

        # 1. create
        unique = secrets.token_hex(4)
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.create(
                CreateUserRequest(
                    email=f"denied-{unique}@test.local",
                    username=f"denied-{unique}",
                    password="test-password-1234",
                    domain_name=domain_fixture,
                    resource_policy=resource_policy_fixture,
                )
            )

        # 2. get
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.get(target_id)

        # 3. search
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.search(SearchUsersRequest())

        # 4. update
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.update(
                target_id,
                UpdateUserRequest(full_name="Denied"),
            )

        # 5. delete
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.delete(DeleteUserRequest(user_id=target_id))

        # 6. purge
        with pytest.raises(PermissionDeniedError):
            await user_registry.user.purge(PurgeUserRequest(user_id=target_id))
