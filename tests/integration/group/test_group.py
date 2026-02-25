from __future__ import annotations

import secrets
from collections.abc import Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.group import (
    AddGroupMembersRequest,
    CreateGroupRequest,
    CreateGroupResponse,
    GroupFilter,
    RemoveGroupMembersRequest,
    SearchGroupsRequest,
    UpdateGroupRequest,
)
from ai.backend.common.dto.manager.query import StringFilter

GroupFactory = Callable[..., Coroutine[Any, Any, CreateGroupResponse]]


@pytest.mark.integration
class TestGroupLifecycle:
    @pytest.mark.asyncio
    async def test_full_group_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
    ) -> None:
        """create -> get -> update -> search (verify updated) -> delete -> verify"""
        unique = secrets.token_hex(4)
        create_result = await group_factory(
            name=f"lifecycle-grp-{unique}",
            description="Lifecycle Test Group",
        )
        group_id = create_result.group.id
        assert create_result.group.name == f"lifecycle-grp-{unique}"
        assert create_result.group.is_active is True

        # Get
        get_result = await admin_registry.group.get(group_id)
        assert get_result.group.id == group_id
        assert get_result.group.name == f"lifecycle-grp-{unique}"

        # Update
        update_result = await admin_registry.group.update(
            group_id,
            UpdateGroupRequest(
                description="Updated via lifecycle test",
            ),
        )
        assert update_result.group.description == "Updated via lifecycle test"

        # Search (verify updated fields)
        search_result = await admin_registry.group.search(
            SearchGroupsRequest(
                filter=GroupFilter(name=StringFilter(contains=f"lifecycle-grp-{unique}")),
            )
        )
        assert search_result.pagination.total == 1
        assert search_result.groups[0].description == "Updated via lifecycle test"

        # Delete (soft)
        delete_result = await admin_registry.group.delete(group_id)
        assert delete_result.deleted is True

        # Verify inactive after delete: get should still work but group is inactive
        after_delete = await admin_registry.group.get(group_id)
        assert after_delete.group.is_active is False


@pytest.mark.integration
class TestGroupMemberLifecycle:
    @pytest.mark.asyncio
    async def test_member_management_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
        regular_user_fixture: Any,
    ) -> None:
        """create group -> add members -> remove members -> verify"""
        create_result = await group_factory()
        group_id = create_result.group.id
        user_id = regular_user_fixture.user_uuid

        # Add member
        add_result = await admin_registry.group.add_members(
            group_id,
            AddGroupMembersRequest(user_ids=[user_id]),
        )
        assert len(add_result.members) == 1
        assert add_result.members[0].user_id == user_id

        # Remove member
        remove_result = await admin_registry.group.remove_members(
            group_id,
            RemoveGroupMembersRequest(user_ids=[user_id]),
        )
        assert remove_result.removed_count == 1


@pytest.mark.integration
class TestGroupPermissionVerification:
    @pytest.mark.asyncio
    async def test_regular_user_denied_admin_endpoints(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
        target_group: CreateGroupResponse,
    ) -> None:
        """Systematically test all methods with user_registry."""
        target_id = target_group.group.id

        # 1. create
        unique = secrets.token_hex(4)
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.create(
                CreateGroupRequest(
                    name=f"denied-group-{unique}",
                    domain_name=domain_fixture,
                    description="Should be denied",
                )
            )

        # 2. get
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.get(target_id)

        # 3. search
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.search(SearchGroupsRequest())

        # 4. update
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.update(
                target_id,
                UpdateGroupRequest(description="Denied"),
            )

        # 5. delete
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.delete(target_id)
