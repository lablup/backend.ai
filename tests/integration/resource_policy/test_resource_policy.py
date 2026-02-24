from __future__ import annotations

import secrets

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.resource_policy.request import (
    CreateKeypairResourcePolicyRequest,
    CreateProjectResourcePolicyRequest,
    CreateUserResourcePolicyRequest,
    DeleteKeypairResourcePolicyRequest,
    DeleteProjectResourcePolicyRequest,
    DeleteUserResourcePolicyRequest,
    KeypairResourcePolicyFilter,
    ProjectResourcePolicyFilter,
    SearchKeypairResourcePoliciesRequest,
    SearchProjectResourcePoliciesRequest,
    SearchUserResourcePoliciesRequest,
    UpdateKeypairResourcePolicyRequest,
    UpdateProjectResourcePolicyRequest,
    UpdateUserResourcePolicyRequest,
    UserResourcePolicyFilter,
)

from .conftest import KeypairPolicyFactory, ProjectPolicyFactory, UserPolicyFactory


@pytest.mark.integration
class TestResourcePolicyLifecycle:
    @pytest.mark.asyncio
    async def test_keypair_policy_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        keypair_policy_factory: KeypairPolicyFactory,
    ) -> None:
        """create -> get -> update -> search (verify update) -> delete -> verify deleted"""
        unique = secrets.token_hex(4)
        name = f"lifecycle-kp-{unique}"

        # Create
        create_result = await keypair_policy_factory(name=name, max_concurrent_sessions=2)
        assert create_result.item.name == name
        assert create_result.item.max_concurrent_sessions == 2

        # Get
        get_result = await admin_registry.resource_policy.get_keypair_policy(name)
        assert get_result.item.name == name

        # Update
        update_result = await admin_registry.resource_policy.update_keypair_policy(
            name, UpdateKeypairResourcePolicyRequest(max_concurrent_sessions=10)
        )
        assert update_result.item.max_concurrent_sessions == 10

        # Search (verify update)
        search_result = await admin_registry.resource_policy.search_keypair_policies(
            SearchKeypairResourcePoliciesRequest(
                filter=KeypairResourcePolicyFilter(name=StringFilter(contains=unique)),
            )
        )
        assert search_result.pagination.total >= 1
        found = [p for p in search_result.items if p.name == name]
        assert len(found) == 1
        assert found[0].max_concurrent_sessions == 10

        # Delete
        delete_result = await admin_registry.resource_policy.delete_keypair_policy(
            DeleteKeypairResourcePolicyRequest(name=name)
        )
        assert delete_result.deleted is True

        # Verify deleted
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_keypair_policy(name)

    @pytest.mark.asyncio
    async def test_user_policy_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        user_policy_factory: UserPolicyFactory,
    ) -> None:
        """create -> get -> update -> search -> delete -> verify deleted"""
        unique = secrets.token_hex(4)
        name = f"lifecycle-user-{unique}"

        create_result = await user_policy_factory(name=name, max_vfolder_count=5)
        assert create_result.item.name == name
        assert create_result.item.max_vfolder_count == 5

        get_result = await admin_registry.resource_policy.get_user_policy(name)
        assert get_result.item.name == name

        update_result = await admin_registry.resource_policy.update_user_policy(
            name, UpdateUserResourcePolicyRequest(max_vfolder_count=20)
        )
        assert update_result.item.max_vfolder_count == 20

        search_result = await admin_registry.resource_policy.search_user_policies(
            SearchUserResourcePoliciesRequest(
                filter=UserResourcePolicyFilter(name=StringFilter(contains=unique)),
            )
        )
        assert search_result.pagination.total >= 1
        found = [p for p in search_result.items if p.name == name]
        assert len(found) == 1
        assert found[0].max_vfolder_count == 20

        delete_result = await admin_registry.resource_policy.delete_user_policy(
            DeleteUserResourcePolicyRequest(name=name)
        )
        assert delete_result.deleted is True

        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_user_policy(name)

    @pytest.mark.asyncio
    async def test_project_policy_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        project_policy_factory: ProjectPolicyFactory,
    ) -> None:
        """create -> get -> update -> search -> delete -> verify deleted"""
        unique = secrets.token_hex(4)
        name = f"lifecycle-proj-{unique}"

        create_result = await project_policy_factory(name=name, max_network_count=3)
        assert create_result.item.name == name
        assert create_result.item.max_network_count == 3

        get_result = await admin_registry.resource_policy.get_project_policy(name)
        assert get_result.item.name == name

        update_result = await admin_registry.resource_policy.update_project_policy(
            name, UpdateProjectResourcePolicyRequest(max_network_count=10)
        )
        assert update_result.item.max_network_count == 10

        search_result = await admin_registry.resource_policy.search_project_policies(
            SearchProjectResourcePoliciesRequest(
                filter=ProjectResourcePolicyFilter(name=StringFilter(contains=unique)),
            )
        )
        assert search_result.pagination.total >= 1
        found = [p for p in search_result.items if p.name == name]
        assert len(found) == 1
        assert found[0].max_network_count == 10

        delete_result = await admin_registry.resource_policy.delete_project_policy(
            DeleteProjectResourcePolicyRequest(name=name)
        )
        assert delete_result.deleted is True

        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_project_policy(name)


@pytest.mark.integration
class TestResourcePolicyPermissionVerification:
    @pytest.mark.asyncio
    async def test_regular_user_denied_on_keypair_endpoints(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.create_keypair_policy(
                CreateKeypairResourcePolicyRequest(name="denied")
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.get_keypair_policy("nonexistent")
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.search_keypair_policies(
                SearchKeypairResourcePoliciesRequest()
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.update_keypair_policy(
                "nonexistent", UpdateKeypairResourcePolicyRequest(max_concurrent_sessions=1)
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.delete_keypair_policy(
                DeleteKeypairResourcePolicyRequest(name="nonexistent")
            )

    @pytest.mark.asyncio
    async def test_regular_user_denied_on_user_endpoints(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.create_user_policy(
                CreateUserResourcePolicyRequest(name="denied")
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.get_user_policy("nonexistent")
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.search_user_policies(
                SearchUserResourcePoliciesRequest()
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.update_user_policy(
                "nonexistent", UpdateUserResourcePolicyRequest(max_vfolder_count=1)
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.delete_user_policy(
                DeleteUserResourcePolicyRequest(name="nonexistent")
            )

    @pytest.mark.asyncio
    async def test_regular_user_denied_on_project_endpoints(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.create_project_policy(
                CreateProjectResourcePolicyRequest(name="denied")
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.get_project_policy("nonexistent")
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.search_project_policies(
                SearchProjectResourcePoliciesRequest()
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.update_project_policy(
                "nonexistent", UpdateProjectResourcePolicyRequest(max_network_count=1)
            )
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.delete_project_policy(
                DeleteProjectResourcePolicyRequest(name="nonexistent")
            )
