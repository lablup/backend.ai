from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.group import (
    AddGroupMembersRequest,
    CreateGroupRequest,
    RemoveGroupMembersRequest,
    UpdateGroupRequest,
)
from ai.backend.common.dto.manager.registry.request import (
    CreateRegistryQuotaReq,
    ReadRegistryQuotaReq,
)
from ai.backend.common.dto.manager.registry.response import RegistryQuotaResponse


class TestGroupRegistryQuota:
    """Tests for registry quota operations via /group/registry-quota endpoints."""

    async def test_admin_creates_registry_quota(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        await admin_registry.group.create_registry_quota(
            CreateRegistryQuotaReq(group_id=str(target_group), quota=100),
        )
        result = await admin_registry.group.read_registry_quota(
            ReadRegistryQuotaReq(group_id=str(target_group)),
        )
        assert isinstance(result, RegistryQuotaResponse)
        assert result.result == 100

    async def test_admin_reads_unset_registry_quota(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        result = await admin_registry.group.read_registry_quota(
            ReadRegistryQuotaReq(group_id=str(target_group)),
        )
        assert isinstance(result, RegistryQuotaResponse)
        assert result.result is None

    async def test_regular_user_cannot_create_registry_quota(
        self,
        user_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.create_registry_quota(
                CreateRegistryQuotaReq(group_id=str(target_group), quota=50),
            )

    async def test_regular_user_cannot_read_registry_quota(
        self,
        user_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.read_registry_quota(
                ReadRegistryQuotaReq(group_id=str(target_group)),
            )


class TestGroupCreate:
    """Tests for group creation via /groups endpoint.

    Currently xfail because the /groups REST routes have not been implemented yet.
    The GroupClient SDK defines these methods but the server-side handlers are missing.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups CRUD routes not yet implemented on server side",
        raises=NotFoundError,
    )
    async def test_admin_creates_group(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        result = await admin_registry.group.create(
            CreateGroupRequest(
                name="test-group-create",
                domain_name=domain_fixture,
                description="Test group created via SDK",
                resource_policy=resource_policy_fixture,
            ),
        )
        assert result.group.name == "test-group-create"


class TestGroupUpdate:
    """Tests for group update via /groups/{id} endpoint.

    Currently xfail because the /groups REST routes have not been implemented yet.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups CRUD routes not yet implemented on server side",
        raises=NotFoundError,
    )
    async def test_admin_updates_group(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        result = await admin_registry.group.update(
            target_group,
            UpdateGroupRequest(name="updated-group-name"),
        )
        assert result.group.name == "updated-group-name"


class TestGroupDelete:
    """Tests for group delete via /groups/{id} endpoint.

    Currently xfail because the /groups REST routes have not been implemented yet.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups CRUD routes not yet implemented on server side",
        raises=NotFoundError,
    )
    async def test_admin_deletes_group(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        result = await admin_registry.group.delete(target_group)
        assert result.deleted is True


class TestGroupMembers:
    """Tests for group member management via /groups/{id}/members endpoints.

    Currently xfail because the /groups REST routes have not been implemented yet.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups member routes not yet implemented on server side",
        raises=NotFoundError,
    )
    async def test_admin_adds_members(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        dummy_user_ids = [uuid.uuid4() for _ in range(5)]
        result = await admin_registry.group.add_members(
            target_group,
            AddGroupMembersRequest(user_ids=dummy_user_ids),
        )
        assert len(result.members) == 5

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups member routes not yet implemented on server side",
        raises=NotFoundError,
    )
    async def test_admin_removes_members(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        dummy_user_ids = [uuid.uuid4()]
        result = await admin_registry.group.remove_members(
            target_group,
            RemoveGroupMembersRequest(user_ids=dummy_user_ids),
        )
        assert result.removed_count >= 0


class TestGroupLifecycle:
    """Full lifecycle integration test: create -> add users -> set quota -> modify -> delete.

    Currently xfail because the /groups CRUD REST routes have not been implemented yet.
    Only the registry-quota portion of the lifecycle is testable.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="REST /groups CRUD routes not yet implemented on server side",
        raises=NotFoundError,
    )
    async def test_full_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        # 1. Create group
        create_result = await admin_registry.group.create(
            CreateGroupRequest(
                name="lifecycle-test-group",
                domain_name=domain_fixture,
                description="Lifecycle test",
                resource_policy=resource_policy_fixture,
            ),
        )
        group_id = create_result.group.id
        assert create_result.group.is_active is True

        # 2. Add users
        user_ids = [uuid.uuid4() for _ in range(3)]
        add_result = await admin_registry.group.add_members(
            group_id, AddGroupMembersRequest(user_ids=user_ids)
        )
        assert len(add_result.members) == 3

        # 3. Set registry quota
        await admin_registry.group.create_registry_quota(
            CreateRegistryQuotaReq(group_id=str(group_id), quota=200),
        )
        quota = await admin_registry.group.read_registry_quota(
            ReadRegistryQuotaReq(group_id=str(group_id)),
        )
        assert quota.result == 200

        # 4. Modify group
        update_result = await admin_registry.group.update(
            group_id, UpdateGroupRequest(description="Updated lifecycle test")
        )
        assert update_result.group.description == "Updated lifecycle test"

        # 5. Delete group
        delete_result = await admin_registry.group.delete(group_id)
        assert delete_result.deleted is True
