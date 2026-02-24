from __future__ import annotations

import secrets
from collections.abc import Callable, Coroutine
from typing import Any

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
from ai.backend.common.dto.manager.resource_policy.response import (
    CreateKeypairResourcePolicyResponse,
    CreateProjectResourcePolicyResponse,
    CreateUserResourcePolicyResponse,
    DeleteKeypairResourcePolicyResponse,
    DeleteProjectResourcePolicyResponse,
    DeleteUserResourcePolicyResponse,
    GetKeypairResourcePolicyResponse,
    GetProjectResourcePolicyResponse,
    GetUserResourcePolicyResponse,
    SearchKeypairResourcePoliciesResponse,
    SearchProjectResourcePoliciesResponse,
    SearchUserResourcePoliciesResponse,
    UpdateKeypairResourcePolicyResponse,
    UpdateProjectResourcePolicyResponse,
    UpdateUserResourcePolicyResponse,
)

KeypairPolicyFactory = Callable[..., Coroutine[Any, Any, CreateKeypairResourcePolicyResponse]]
UserPolicyFactory = Callable[..., Coroutine[Any, Any, CreateUserResourcePolicyResponse]]
ProjectPolicyFactory = Callable[..., Coroutine[Any, Any, CreateProjectResourcePolicyResponse]]


# ---- Keypair Resource Policy ----


class TestKeypairResourcePolicyCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_keypair_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        keypair_policy_factory: KeypairPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await keypair_policy_factory(name=f"test-kp-{unique}")
        assert isinstance(result, CreateKeypairResourcePolicyResponse)
        assert result.item.name == f"test-kp-{unique}"

    @pytest.mark.asyncio
    async def test_admin_creates_keypair_policy_with_custom_values(
        self,
        admin_registry: BackendAIClientRegistry,
        keypair_policy_factory: KeypairPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await keypair_policy_factory(
            name=f"test-kp-custom-{unique}",
            max_concurrent_sessions=5,
            idle_timeout=3600,
            max_containers_per_session=2,
        )
        assert result.item.max_concurrent_sessions == 5
        assert result.item.idle_timeout == 3600
        assert result.item.max_containers_per_session == 2

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_keypair_policy(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.create_keypair_policy(
                CreateKeypairResourcePolicyRequest(name="denied-kp-policy")
            )


class TestKeypairResourcePolicyGet:
    @pytest.mark.asyncio
    async def test_admin_gets_keypair_policy_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_keypair_policy: CreateKeypairResourcePolicyResponse,
    ) -> None:
        get_result = await admin_registry.resource_policy.get_keypair_policy(
            target_keypair_policy.item.name
        )
        assert isinstance(get_result, GetKeypairResourcePolicyResponse)
        assert get_result.item.name == target_keypair_policy.item.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_keypair_policy_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_keypair_policy(
                "nonexistent-kp-policy-xyz-12345"
            )


class TestKeypairResourcePolicySearch:
    @pytest.mark.asyncio
    async def test_admin_searches_keypair_policies(
        self,
        admin_registry: BackendAIClientRegistry,
        keypair_policy_factory: KeypairPolicyFactory,
    ) -> None:
        await keypair_policy_factory()
        result = await admin_registry.resource_policy.search_keypair_policies(
            SearchKeypairResourcePoliciesRequest()
        )
        assert isinstance(result, SearchKeypairResourcePoliciesResponse)
        assert result.pagination.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        keypair_policy_factory: KeypairPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"searchable-kp-{unique}"
        await keypair_policy_factory(name=marker)
        result = await admin_registry.resource_policy.search_keypair_policies(
            SearchKeypairResourcePoliciesRequest(
                filter=KeypairResourcePolicyFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(p.name == marker for p in result.items)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.resource_policy.search_keypair_policies(
            SearchKeypairResourcePoliciesRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.items) <= 1


class TestKeypairResourcePolicyUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_keypair_policy_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_keypair_policy: CreateKeypairResourcePolicyResponse,
    ) -> None:
        update_result = await admin_registry.resource_policy.update_keypair_policy(
            target_keypair_policy.item.name,
            UpdateKeypairResourcePolicyRequest(
                max_concurrent_sessions=10,
                idle_timeout=7200,
            ),
        )
        assert isinstance(update_result, UpdateKeypairResourcePolicyResponse)
        assert update_result.item.max_concurrent_sessions == 10
        assert update_result.item.idle_timeout == 7200
        assert update_result.item.name == target_keypair_policy.item.name

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_keypair_policy(
        self,
        user_registry: BackendAIClientRegistry,
        target_keypair_policy: CreateKeypairResourcePolicyResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.update_keypair_policy(
                target_keypair_policy.item.name,
                UpdateKeypairResourcePolicyRequest(max_concurrent_sessions=99),
            )


class TestKeypairResourcePolicyDelete:
    @pytest.mark.asyncio
    async def test_admin_deletes_keypair_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        keypair_policy_factory: KeypairPolicyFactory,
    ) -> None:
        r = await keypair_policy_factory()
        delete_result = await admin_registry.resource_policy.delete_keypair_policy(
            DeleteKeypairResourcePolicyRequest(name=r.item.name)
        )
        assert isinstance(delete_result, DeleteKeypairResourcePolicyResponse)
        assert delete_result.deleted is True
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_keypair_policy(r.item.name)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_keypair_policy(
        self,
        user_registry: BackendAIClientRegistry,
        target_keypair_policy: CreateKeypairResourcePolicyResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.delete_keypair_policy(
                DeleteKeypairResourcePolicyRequest(name=target_keypair_policy.item.name)
            )


# ---- User Resource Policy ----


class TestUserResourcePolicyCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_user_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        user_policy_factory: UserPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_policy_factory(name=f"test-user-{unique}")
        assert isinstance(result, CreateUserResourcePolicyResponse)
        assert result.item.name == f"test-user-{unique}"

    @pytest.mark.asyncio
    async def test_admin_creates_user_policy_with_custom_values(
        self,
        admin_registry: BackendAIClientRegistry,
        user_policy_factory: UserPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await user_policy_factory(
            name=f"test-user-custom-{unique}",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_customized_image_count=5,
        )
        assert result.item.max_vfolder_count == 10
        assert result.item.max_quota_scope_size == 1073741824
        assert result.item.max_customized_image_count == 5

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_user_policy(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.create_user_policy(
                CreateUserResourcePolicyRequest(name="denied-user-policy")
            )


class TestUserResourcePolicyGet:
    @pytest.mark.asyncio
    async def test_admin_gets_user_policy_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user_policy: CreateUserResourcePolicyResponse,
    ) -> None:
        get_result = await admin_registry.resource_policy.get_user_policy(
            target_user_policy.item.name
        )
        assert isinstance(get_result, GetUserResourcePolicyResponse)
        assert get_result.item.name == target_user_policy.item.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_policy_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_user_policy(
                "nonexistent-user-policy-xyz-12345"
            )


class TestUserResourcePolicySearch:
    @pytest.mark.asyncio
    async def test_admin_searches_user_policies(
        self,
        admin_registry: BackendAIClientRegistry,
        user_policy_factory: UserPolicyFactory,
    ) -> None:
        await user_policy_factory()
        result = await admin_registry.resource_policy.search_user_policies(
            SearchUserResourcePoliciesRequest()
        )
        assert isinstance(result, SearchUserResourcePoliciesResponse)
        assert result.pagination.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        user_policy_factory: UserPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"searchable-user-{unique}"
        await user_policy_factory(name=marker)
        result = await admin_registry.resource_policy.search_user_policies(
            SearchUserResourcePoliciesRequest(
                filter=UserResourcePolicyFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(p.name == marker for p in result.items)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.resource_policy.search_user_policies(
            SearchUserResourcePoliciesRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.items) <= 1


class TestUserResourcePolicyUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_user_policy_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_user_policy: CreateUserResourcePolicyResponse,
    ) -> None:
        update_result = await admin_registry.resource_policy.update_user_policy(
            target_user_policy.item.name,
            UpdateUserResourcePolicyRequest(
                max_vfolder_count=20,
                max_quota_scope_size=2147483648,
            ),
        )
        assert isinstance(update_result, UpdateUserResourcePolicyResponse)
        assert update_result.item.max_vfolder_count == 20
        assert update_result.item.max_quota_scope_size == 2147483648
        assert update_result.item.name == target_user_policy.item.name

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_user_policy(
        self,
        user_registry: BackendAIClientRegistry,
        target_user_policy: CreateUserResourcePolicyResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.update_user_policy(
                target_user_policy.item.name,
                UpdateUserResourcePolicyRequest(max_vfolder_count=99),
            )


class TestUserResourcePolicyDelete:
    @pytest.mark.asyncio
    async def test_admin_deletes_user_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        user_policy_factory: UserPolicyFactory,
    ) -> None:
        r = await user_policy_factory()
        delete_result = await admin_registry.resource_policy.delete_user_policy(
            DeleteUserResourcePolicyRequest(name=r.item.name)
        )
        assert isinstance(delete_result, DeleteUserResourcePolicyResponse)
        assert delete_result.deleted is True
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_user_policy(r.item.name)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_user_policy(
        self,
        user_registry: BackendAIClientRegistry,
        target_user_policy: CreateUserResourcePolicyResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.delete_user_policy(
                DeleteUserResourcePolicyRequest(name=target_user_policy.item.name)
            )


# ---- Project Resource Policy ----


class TestProjectResourcePolicyCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_project_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        project_policy_factory: ProjectPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await project_policy_factory(name=f"test-proj-{unique}")
        assert isinstance(result, CreateProjectResourcePolicyResponse)
        assert result.item.name == f"test-proj-{unique}"

    @pytest.mark.asyncio
    async def test_admin_creates_project_policy_with_custom_values(
        self,
        admin_registry: BackendAIClientRegistry,
        project_policy_factory: ProjectPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await project_policy_factory(
            name=f"test-proj-custom-{unique}",
            max_vfolder_count=10,
            max_quota_scope_size=1073741824,
            max_network_count=5,
        )
        assert result.item.max_vfolder_count == 10
        assert result.item.max_quota_scope_size == 1073741824
        assert result.item.max_network_count == 5

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_project_policy(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.create_project_policy(
                CreateProjectResourcePolicyRequest(name="denied-proj-policy")
            )


class TestProjectResourcePolicyGet:
    @pytest.mark.asyncio
    async def test_admin_gets_project_policy_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_project_policy: CreateProjectResourcePolicyResponse,
    ) -> None:
        get_result = await admin_registry.resource_policy.get_project_policy(
            target_project_policy.item.name
        )
        assert isinstance(get_result, GetProjectResourcePolicyResponse)
        assert get_result.item.name == target_project_policy.item.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_project_policy_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_project_policy(
                "nonexistent-proj-policy-xyz-12345"
            )


class TestProjectResourcePolicySearch:
    @pytest.mark.asyncio
    async def test_admin_searches_project_policies(
        self,
        admin_registry: BackendAIClientRegistry,
        project_policy_factory: ProjectPolicyFactory,
    ) -> None:
        await project_policy_factory()
        result = await admin_registry.resource_policy.search_project_policies(
            SearchProjectResourcePoliciesRequest()
        )
        assert isinstance(result, SearchProjectResourcePoliciesResponse)
        assert result.pagination.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        project_policy_factory: ProjectPolicyFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"searchable-proj-{unique}"
        await project_policy_factory(name=marker)
        result = await admin_registry.resource_policy.search_project_policies(
            SearchProjectResourcePoliciesRequest(
                filter=ProjectResourcePolicyFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(p.name == marker for p in result.items)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.resource_policy.search_project_policies(
            SearchProjectResourcePoliciesRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.items) <= 1


class TestProjectResourcePolicyUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_project_policy_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_project_policy: CreateProjectResourcePolicyResponse,
    ) -> None:
        update_result = await admin_registry.resource_policy.update_project_policy(
            target_project_policy.item.name,
            UpdateProjectResourcePolicyRequest(
                max_vfolder_count=20,
                max_network_count=10,
            ),
        )
        assert isinstance(update_result, UpdateProjectResourcePolicyResponse)
        assert update_result.item.max_vfolder_count == 20
        assert update_result.item.max_network_count == 10
        assert update_result.item.name == target_project_policy.item.name

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_project_policy(
        self,
        user_registry: BackendAIClientRegistry,
        target_project_policy: CreateProjectResourcePolicyResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.update_project_policy(
                target_project_policy.item.name,
                UpdateProjectResourcePolicyRequest(max_network_count=99),
            )


class TestProjectResourcePolicyDelete:
    @pytest.mark.asyncio
    async def test_admin_deletes_project_policy(
        self,
        admin_registry: BackendAIClientRegistry,
        project_policy_factory: ProjectPolicyFactory,
    ) -> None:
        r = await project_policy_factory()
        delete_result = await admin_registry.resource_policy.delete_project_policy(
            DeleteProjectResourcePolicyRequest(name=r.item.name)
        )
        assert isinstance(delete_result, DeleteProjectResourcePolicyResponse)
        assert delete_result.deleted is True
        with pytest.raises(NotFoundError):
            await admin_registry.resource_policy.get_project_policy(r.item.name)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_project_policy(
        self,
        user_registry: BackendAIClientRegistry,
        target_project_policy: CreateProjectResourcePolicyResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.resource_policy.delete_project_policy(
                DeleteProjectResourcePolicyRequest(name=target_project_policy.item.name)
            )
