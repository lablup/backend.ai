from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.group import (
    AddGroupMembersRequest,
    AddGroupMembersResponse,
    CreateGroupRequest,
    CreateGroupResponse,
    DeleteGroupResponse,
    GetGroupResponse,
    GroupFilter,
    RemoveGroupMembersRequest,
    RemoveGroupMembersResponse,
    SearchGroupsRequest,
    SearchGroupsResponse,
    UpdateGroupRequest,
    UpdateGroupResponse,
)
from ai.backend.common.dto.manager.query import StringFilter

GroupFactory = Callable[..., Coroutine[Any, Any, CreateGroupResponse]]


class TestGroupCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_group(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await group_factory(
            name=f"test-group-{unique}",
            description=f"Test group {unique}",
        )
        assert isinstance(result, CreateGroupResponse)
        assert result.group.name == f"test-group-{unique}"
        assert result.group.description == f"Test group {unique}"
        assert result.group.is_active is True

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_group(
        self,
        user_registry: BackendAIClientRegistry,
        domain_for_group_fixture: str,
    ) -> None:
        unique = secrets.token_hex(4)
        request = CreateGroupRequest(
            name=f"denied-group-{unique}",
            domain_name=domain_for_group_fixture,
            description="Should be denied",
        )
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.create(request)


class TestGroupGet:
    @pytest.mark.asyncio
    async def test_admin_gets_group_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: CreateGroupResponse,
    ) -> None:
        get_result = await admin_registry.group.get(target_group.group.id)
        assert isinstance(get_result, GetGroupResponse)
        assert get_result.group.id == target_group.group.id
        assert get_result.group.name == target_group.group.name
        assert get_result.group.description == target_group.group.description

    @pytest.mark.asyncio
    async def test_get_nonexistent_group_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.group.get(uuid.uuid4())


class TestGroupSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_groups(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
    ) -> None:
        await group_factory()
        result = await admin_registry.group.search(SearchGroupsRequest())
        assert isinstance(result, SearchGroupsResponse)
        assert result.pagination.total >= 1
        assert len(result.groups) >= 1

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"searchable-grp-{unique}"
        await group_factory(name=marker, description=f"Searchable group {unique}")
        result = await admin_registry.group.search(
            SearchGroupsRequest(
                filter=GroupFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(g.name == marker for g in result.groups)

    @pytest.mark.asyncio
    async def test_search_with_domain_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
        domain_for_group_fixture: str,
    ) -> None:
        await group_factory()
        result = await admin_registry.group.search(
            SearchGroupsRequest(
                filter=GroupFilter(
                    domain_name=StringFilter(equals=domain_for_group_fixture),
                ),
            )
        )
        assert result.pagination.total >= 1
        assert all(g.domain_name == domain_for_group_fixture for g in result.groups)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.group.search(
            SearchGroupsRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.groups) <= 1

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_groups(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.search(SearchGroupsRequest())


class TestGroupUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_group_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: CreateGroupResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        update_result = await admin_registry.group.update(
            target_group.group.id,
            UpdateGroupRequest(
                description=f"Updated description {unique}",
            ),
        )
        assert isinstance(update_result, UpdateGroupResponse)
        assert update_result.group.description == f"Updated description {unique}"
        assert update_result.group.id == target_group.group.id

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_group(
        self,
        user_registry: BackendAIClientRegistry,
        target_group: CreateGroupResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.update(
                target_group.group.id,
                UpdateGroupRequest(description="Denied"),
            )


class TestGroupDelete:
    @pytest.mark.asyncio
    async def test_admin_deletes_group(
        self,
        admin_registry: BackendAIClientRegistry,
        group_factory: GroupFactory,
    ) -> None:
        r = await group_factory()
        delete_result = await admin_registry.group.delete(r.group.id)
        assert isinstance(delete_result, DeleteGroupResponse)
        assert delete_result.deleted is True

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_group(
        self,
        user_registry: BackendAIClientRegistry,
        target_group: CreateGroupResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.group.delete(target_group.group.id)


class TestGroupMembers:
    @pytest.mark.asyncio
    async def test_admin_adds_members(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: CreateGroupResponse,
        regular_user_fixture: Any,
    ) -> None:
        user_id = regular_user_fixture.user_uuid
        result = await admin_registry.group.add_members(
            target_group.group.id,
            AddGroupMembersRequest(user_ids=[user_id]),
        )
        assert isinstance(result, AddGroupMembersResponse)
        assert len(result.members) == 1
        assert result.members[0].user_id == user_id
        assert result.members[0].group_id == target_group.group.id

    @pytest.mark.asyncio
    async def test_admin_removes_members(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: CreateGroupResponse,
        regular_user_fixture: Any,
    ) -> None:
        user_id = regular_user_fixture.user_uuid
        # First add the member
        await admin_registry.group.add_members(
            target_group.group.id,
            AddGroupMembersRequest(user_ids=[user_id]),
        )
        # Then remove
        result = await admin_registry.group.remove_members(
            target_group.group.id,
            RemoveGroupMembersRequest(user_ids=[user_id]),
        )
        assert isinstance(result, RemoveGroupMembersResponse)
        assert result.removed_count == 1
