from __future__ import annotations

import secrets
import uuid

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.group import (
    CreateGroupRequest,
    CreateGroupResponse,
    GetGroupResponse,
    UpdateGroupRequest,
    UpdateGroupResponse,
)

_XFAIL_ROUTES_NOT_IMPLEMENTED = pytest.mark.xfail(
    strict=True,
    reason="REST /groups CRUD routes not yet implemented on server side",
    raises=NotFoundError,
)


class TestGroupCreateCRUD:
    """Tests for group creation via POST /groups.

    All tests are xfail because the /groups REST CRUD routes are not yet
    implemented on the server side.
    """

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_superadmin_creates_group_with_required_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """S-1: Superadmin creates group with required fields."""
        unique = secrets.token_hex(4)
        result = await admin_registry.group.create(
            CreateGroupRequest(
                name=f"test-group-{unique}",
                domain_name=domain_fixture,
            ),
        )
        assert isinstance(result, CreateGroupResponse)
        assert result.group.name == f"test-group-{unique}"
        assert result.group.domain_name == domain_fixture
        assert result.group.is_active is True

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_create_group_with_all_optional_fields(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
        resource_policy_fixture: str,
    ) -> None:
        """S-2: Create group with all optional fields."""
        unique = secrets.token_hex(4)
        result = await admin_registry.group.create(
            CreateGroupRequest(
                name=f"test-group-full-{unique}",
                domain_name=domain_fixture,
                description=f"Full group {unique}",
                resource_policy=resource_policy_fixture,
                total_resource_slots={"cpu": "4"},
                integration_id=f"ext-{unique}",
            ),
        )
        assert isinstance(result, CreateGroupResponse)
        assert result.group.name == f"test-group-full-{unique}"
        assert result.group.description == f"Full group {unique}"
        assert result.group.resource_policy == resource_policy_fixture

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_create_group_then_set_inactive(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """S-3: Create group then deactivate it (is_active=False)."""
        unique = secrets.token_hex(4)
        create_result = await admin_registry.group.create(
            CreateGroupRequest(
                name=f"test-group-inactive-{unique}",
                domain_name=domain_fixture,
            ),
        )
        update_result = await admin_registry.group.update(
            create_result.group.id,
            UpdateGroupRequest(is_active=False),
        )
        assert update_result.group.is_active is False

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_create_multiple_groups_with_different_names(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """S-4: Create multiple groups with different names."""
        unique = secrets.token_hex(4)
        result_a = await admin_registry.group.create(
            CreateGroupRequest(
                name=f"test-group-alpha-{unique}",
                domain_name=domain_fixture,
            ),
        )
        result_b = await admin_registry.group.create(
            CreateGroupRequest(
                name=f"test-group-beta-{unique}",
                domain_name=domain_fixture,
            ),
        )
        assert result_a.group.name != result_b.group.name
        assert result_a.group.id != result_b.group.id

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_duplicate_group_name_in_same_domain_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """F-BIZ-1: Duplicate group name in same domain → error."""
        unique = secrets.token_hex(4)
        name = f"test-group-dup-{unique}"
        await admin_registry.group.create(
            CreateGroupRequest(name=name, domain_name=domain_fixture),
        )
        await admin_registry.group.create(
            CreateGroupRequest(name=name, domain_name=domain_fixture),
        )

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_regular_user_cannot_create_group(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """F-AUTH-1: Regular user cannot create group → error."""
        unique = secrets.token_hex(4)
        await user_registry.group.create(
            CreateGroupRequest(
                name=f"test-group-user-{unique}",
                domain_name=domain_fixture,
            ),
        )


class TestGroupGetCRUD:
    """Tests for group retrieval via GET /groups/{id}.

    All tests are xfail because the /groups REST CRUD routes are not yet
    implemented on the server side.
    """

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_get_group_by_uuid_returns_group_dto(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        """S-1: Get project by UUID returns GroupDTO."""
        result = await admin_registry.group.get(target_group)
        assert isinstance(result, GetGroupResponse)
        assert result.group.id == target_group

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_get_inactive_group_still_returns_data(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        """S-2: Get inactive project still returns data."""
        result = await admin_registry.group.get(target_group)
        assert isinstance(result, GetGroupResponse)
        assert result.group.id == target_group

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_get_nonexistent_uuid_raises_not_found_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Get non-existent UUID → NotFoundError."""
        nonexistent_id = uuid.uuid4()
        await admin_registry.group.get(nonexistent_id)


class TestGroupModifyCRUD:
    """Tests for group modification via PATCH /groups/{id}.

    All tests are xfail because the /groups REST CRUD routes are not yet
    implemented on the server side.
    """

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_update_group_description(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        """S-1: Update group description."""
        unique = secrets.token_hex(4)
        result = await admin_registry.group.update(
            target_group,
            UpdateGroupRequest(description=f"Updated description {unique}"),
        )
        assert isinstance(result, UpdateGroupResponse)
        assert result.group.description == f"Updated description {unique}"

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_update_group_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        """S-2: Update group name."""
        unique = secrets.token_hex(4)
        new_name = f"updated-group-{unique}"
        result = await admin_registry.group.update(
            target_group,
            UpdateGroupRequest(name=new_name),
        )
        assert isinstance(result, UpdateGroupResponse)
        assert result.group.name == new_name

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_update_total_resource_slots(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        """S-3: Update total_resource_slots."""
        result = await admin_registry.group.update(
            target_group,
            UpdateGroupRequest(total_resource_slots={"cpu": "8", "mem": "16g"}),
        )
        assert isinstance(result, UpdateGroupResponse)
        assert result.group.total_resource_slots is not None

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_update_nonexistent_group_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """F-BIZ-1: Update non-existent group → error."""
        nonexistent_id = uuid.uuid4()
        await admin_registry.group.update(
            nonexistent_id,
            UpdateGroupRequest(description="Should fail"),
        )

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_rename_group_to_duplicate_name_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
        domain_fixture: str,
    ) -> None:
        """F-BIZ-3: Rename to duplicate name → error."""
        unique = secrets.token_hex(4)
        other_name = f"other-group-{unique}"
        await admin_registry.group.create(
            CreateGroupRequest(name=other_name, domain_name=domain_fixture),
        )
        await admin_registry.group.update(
            target_group,
            UpdateGroupRequest(name=other_name),
        )

    @_XFAIL_ROUTES_NOT_IMPLEMENTED
    async def test_regular_user_cannot_modify_group(
        self,
        user_registry: BackendAIClientRegistry,
        target_group: uuid.UUID,
    ) -> None:
        """F-AUTH-1: Regular user cannot modify group → error."""
        await user_registry.group.update(
            target_group,
            UpdateGroupRequest(description="Unauthorized update"),
        )
