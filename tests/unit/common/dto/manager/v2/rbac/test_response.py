"""Tests for ai.backend.common.dto.manager.v2.rbac.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    RoleStatus,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    CreateRolePayload,
    DeleteRolePayload,
    PurgeRolePayload,
    RoleNode,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionSummary


class TestRoleNodeCreation:
    """Tests for RoleNode model creation with all fields."""

    def test_creation_with_all_fields(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="Admin",
            description="Administrator role",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            permissions=[],
        )
        assert node.id == role_id
        assert node.name == "Admin"
        assert node.description == "Administrator role"
        assert node.source == RoleSource.CUSTOM
        assert node.status == RoleStatus.ACTIVE
        assert node.created_at == now
        assert node.updated_at == now
        assert node.deleted_at is None
        assert node.permissions == []

    def test_creation_with_minimal_fields(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert node.id == role_id
        assert node.description is None
        assert node.deleted_at is None
        assert node.permissions == []

    def test_description_is_none_by_default(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="TestRole",
            source=RoleSource.SYSTEM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert node.description is None

    def test_description_explicit_none(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="TestRole",
            description=None,
            source=RoleSource.SYSTEM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert node.description is None

    def test_deleted_at_can_be_datetime(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="DeletedRole",
            source=RoleSource.CUSTOM,
            status=RoleStatus.DELETED,
            created_at=now,
            updated_at=now,
            deleted_at=now,
        )
        assert node.deleted_at == now
        assert node.status == RoleStatus.DELETED

    def test_system_source(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="SystemRole",
            source=RoleSource.SYSTEM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert node.source == RoleSource.SYSTEM

    def test_inactive_status(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="InactiveRole",
            source=RoleSource.CUSTOM,
            status=RoleStatus.INACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert node.status == RoleStatus.INACTIVE


class TestRoleNodeWithPermissions:
    """Tests for RoleNode with nested PermissionSummary list."""

    def test_permissions_default_empty_list(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert node.permissions == []

    def test_permissions_with_single_entry(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        perm = PermissionSummary(
            entity_type=EntityType.SESSION,
            operation=OperationType.READ,
        )
        node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            permissions=[perm],
        )
        assert len(node.permissions) == 1
        assert node.permissions[0].entity_type == EntityType.SESSION
        assert node.permissions[0].operation == OperationType.READ

    def test_permissions_with_multiple_entries(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        perms = [
            PermissionSummary(entity_type=EntityType.SESSION, operation=OperationType.READ),
            PermissionSummary(entity_type=EntityType.VFOLDER, operation=OperationType.CREATE),
            PermissionSummary(entity_type=EntityType.IMAGE, operation=OperationType.UPDATE),
        ]
        node = RoleNode(
            id=role_id,
            name="PowerUser",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            permissions=perms,
        )
        assert len(node.permissions) == 3
        assert node.permissions[1].entity_type == EntityType.VFOLDER

    def test_permissions_serialize_to_nested_json(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        perm = PermissionSummary(
            entity_type=EntityType.SESSION,
            operation=OperationType.READ,
        )
        node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            permissions=[perm],
        )
        data = json.loads(node.model_dump_json())
        assert "permissions" in data
        assert isinstance(data["permissions"], list)
        assert len(data["permissions"]) == 1
        assert data["permissions"][0]["entity_type"] == EntityType.SESSION
        assert data["permissions"][0]["operation"] == OperationType.READ

    def test_permissions_nested_structure_preserved_in_round_trip(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        perms = [
            PermissionSummary(entity_type=EntityType.SESSION, operation=OperationType.READ),
            PermissionSummary(entity_type=EntityType.VFOLDER, operation=OperationType.CREATE),
        ]
        node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            permissions=perms,
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert len(restored.permissions) == 2
        assert restored.permissions[0].entity_type == EntityType.SESSION
        assert restored.permissions[1].entity_type == EntityType.VFOLDER


class TestCreateRolePayload:
    """Tests for CreateRolePayload model."""

    def test_creation_with_role_node(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        payload = CreateRolePayload(role=role_node)
        assert payload.role.name == "Admin"
        assert payload.role.id == role_id

    def test_role_name_accessible_via_payload(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="Admin",
            description="Admin role",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        payload = CreateRolePayload(role=role_node)
        assert payload.role.name == "Admin"
        assert payload.role.description == "Admin role"

    def test_round_trip_serialization(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        payload = CreateRolePayload(role=role_node)
        json_str = payload.model_dump_json()
        restored = CreateRolePayload.model_validate_json(json_str)
        assert restored.role.id == role_id
        assert restored.role.name == "Admin"
        assert restored.role.source == RoleSource.CUSTOM

    def test_nested_permissions_in_payload(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        perm = PermissionSummary(
            entity_type=EntityType.SESSION,
            operation=OperationType.READ,
        )
        role_node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            permissions=[perm],
        )
        payload = CreateRolePayload(role=role_node)
        assert len(payload.role.permissions) == 1
        assert payload.role.permissions[0].entity_type == EntityType.SESSION


class TestUpdateRolePayload:
    """Tests for UpdateRolePayload model."""

    def test_creation_with_role_node(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="UpdatedAdmin",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        payload = UpdateRolePayload(role=role_node)
        assert payload.role.name == "UpdatedAdmin"
        assert payload.role.id == role_id

    def test_round_trip_serialization(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="UpdatedAdmin",
            description="Updated description",
            source=RoleSource.CUSTOM,
            status=RoleStatus.INACTIVE,
            created_at=now,
            updated_at=now,
        )
        payload = UpdateRolePayload(role=role_node)
        json_str = payload.model_dump_json()
        restored = UpdateRolePayload.model_validate_json(json_str)
        assert restored.role.id == role_id
        assert restored.role.name == "UpdatedAdmin"
        assert restored.role.description == "Updated description"
        assert restored.role.status == RoleStatus.INACTIVE


class TestDeleteRolePayload:
    """Tests for DeleteRolePayload model."""

    def test_creation_with_uuid(self) -> None:
        role_id = uuid.uuid4()
        payload = DeleteRolePayload(id=role_id)
        assert payload.id == role_id

    def test_id_is_uuid_instance(self) -> None:
        role_id = uuid.uuid4()
        payload = DeleteRolePayload(id=role_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        role_id = uuid.uuid4()
        payload = DeleteRolePayload.model_validate({"id": str(role_id)})
        assert payload.id == role_id

    def test_round_trip_serialization(self) -> None:
        role_id = uuid.uuid4()
        payload = DeleteRolePayload(id=role_id)
        json_str = payload.model_dump_json()
        restored = DeleteRolePayload.model_validate_json(json_str)
        assert restored.id == role_id

    def test_id_matches_input(self) -> None:
        role_id = uuid.uuid4()
        payload = DeleteRolePayload(id=role_id)
        assert payload.id == role_id


class TestPurgeRolePayload:
    """Tests for PurgeRolePayload model."""

    def test_creation_with_uuid(self) -> None:
        role_id = uuid.uuid4()
        payload = PurgeRolePayload(id=role_id)
        assert payload.id == role_id

    def test_id_is_uuid_instance(self) -> None:
        role_id = uuid.uuid4()
        payload = PurgeRolePayload(id=role_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        role_id = uuid.uuid4()
        payload = PurgeRolePayload.model_validate({"id": str(role_id)})
        assert payload.id == role_id

    def test_round_trip_serialization(self) -> None:
        role_id = uuid.uuid4()
        payload = PurgeRolePayload(id=role_id)
        json_str = payload.model_dump_json()
        restored = PurgeRolePayload.model_validate_json(json_str)
        assert restored.id == role_id


class TestRoleNodeRoundTrip:
    """Tests for RoleNode serialization round-trip."""

    def test_round_trip_with_all_fields(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="Admin",
            description="Admin role",
            source=RoleSource.CUSTOM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            permissions=[
                PermissionSummary(entity_type=EntityType.SESSION, operation=OperationType.READ),
            ],
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.description == node.description
        assert restored.source == node.source
        assert restored.status == node.status
        assert restored.deleted_at is None
        assert len(restored.permissions) == 1
        assert restored.permissions[0].entity_type == EntityType.SESSION

    def test_round_trip_with_deleted_at(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="DeletedRole",
            source=RoleSource.CUSTOM,
            status=RoleStatus.DELETED,
            created_at=now,
            updated_at=now,
            deleted_at=now,
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert restored.id == role_id
        assert restored.status == RoleStatus.DELETED
        assert restored.deleted_at is not None

    def test_round_trip_empty_permissions(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="BasicRole",
            source=RoleSource.SYSTEM,
            status=RoleStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            permissions=[],
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert restored.permissions == []
