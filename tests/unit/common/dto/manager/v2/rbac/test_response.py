"""Tests for ai.backend.common.dto.manager.v2.rbac.response module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.dto.manager.v2.rbac.response import (
    CreateRolePayload,
    DeleteRolePayload,
    PermissionNode,
    PurgeRolePayload,
    RoleNode,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    OperationTypeDTO,
    PermissionBitDTO,
    RoleSourceDTO,
    RoleStatusDTO,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed

_SCOPE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class TestRoleNodeCreation:
    """Tests for RoleNode model creation with all fields."""

    def test_creation_with_all_fields(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="Admin",
            description="Administrator role",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
            deleted_at=None,
        )
        assert node.id == role_id
        assert node.name == "Admin"
        assert node.description == "Administrator role"
        assert node.source == RoleSourceDTO.CUSTOM
        assert node.status == RoleStatusDTO.ACTIVE
        assert node.created_at == now
        assert node.updated_at == now
        assert node.deleted_at is None

    def test_creation_with_minimal_fields(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        assert node.id == role_id
        assert node.description is None
        assert node.deleted_at is None

    def test_description_is_none_by_default(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="TestRole",
            source=RoleSourceDTO.SYSTEM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        assert node.description is None

    def test_description_explicit_none(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="TestRole",
            description=None,
            source=RoleSourceDTO.SYSTEM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        assert node.description is None

    def test_deleted_at_can_be_datetime(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="DeletedRole",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.DELETED,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
            deleted_at=now,
        )
        assert node.deleted_at == now
        assert node.status == RoleStatusDTO.DELETED

    def test_system_source(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="SystemRole",
            source=RoleSourceDTO.SYSTEM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        assert node.source == RoleSourceDTO.SYSTEM

    def test_inactive_status(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="InactiveRole",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.INACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        assert node.status == RoleStatusDTO.INACTIVE


class TestCreateRolePayload:
    """Tests for CreateRolePayload model."""

    def test_creation_with_role_node(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="Admin",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
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
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
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
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        payload = CreateRolePayload(role=role_node)
        json_str = payload.model_dump_json()
        restored = CreateRolePayload.model_validate_json(json_str)
        assert restored.role.id == role_id
        assert restored.role.name == "Admin"
        assert restored.role.source == RoleSourceDTO.CUSTOM


class TestUpdateRolePayload:
    """Tests for UpdateRolePayload model."""

    def test_creation_with_role_node(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        role_node = RoleNode(
            id=role_id,
            name="UpdatedAdmin",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
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
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.INACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        payload = UpdateRolePayload(role=role_node)
        json_str = payload.model_dump_json()
        restored = UpdateRolePayload.model_validate_json(json_str)
        assert restored.role.id == role_id
        assert restored.role.name == "UpdatedAdmin"
        assert restored.role.description == "Updated description"
        assert restored.role.status == RoleStatusDTO.INACTIVE


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
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
            deleted_at=None,
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.description == node.description
        assert restored.source == node.source
        assert restored.status == node.status
        assert restored.deleted_at is None

    def test_round_trip_with_deleted_at(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="DeletedRole",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.DELETED,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
            deleted_at=now,
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert restored.id == role_id
        assert restored.status == RoleStatusDTO.DELETED
        assert restored.deleted_at is not None

    def test_round_trip_minimal_fields(self) -> None:
        role_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=role_id,
            name="BasicRole",
            source=RoleSourceDTO.SYSTEM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("project"),
            scope_id=_SCOPE_ID,
        )
        json_str = node.model_dump_json()
        restored = RoleNode.model_validate_json(json_str)
        assert restored.id == role_id
        assert restored.name == "BasicRole"


class TestRoleNodeScope:
    """The role names the one scope it belongs to."""

    def test_the_scope_is_required(self) -> None:
        now = datetime.now(tz=UTC).isoformat()
        with pytest.raises(BackendAISchemaValidationFailed):
            RoleNode.model_validate({
                "id": str(uuid.uuid4()),
                "name": "Scopeless",
                "source": RoleSourceDTO.CUSTOM.value,
                "status": RoleStatusDTO.ACTIVE.value,
                "created_at": now,
                "updated_at": now,
            })

    def test_the_scope_survives_a_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        node = RoleNode(
            id=uuid.uuid4(),
            name="Scoped",
            source=RoleSourceDTO.CUSTOM,
            status=RoleStatusDTO.ACTIVE,
            created_at=now,
            updated_at=now,
            scope_type=EntityType("domain"),
            scope_id=_SCOPE_ID,
        )

        restored = RoleNode.model_validate_json(node.model_dump_json())

        assert restored.scope_type == "domain"
        assert restored.scope_id == _SCOPE_ID


class TestPermissionNodeBit:
    """A permission row names the bit it holds, and keeps the deprecated action name."""

    def _node(self, permission: PermissionBitDTO, operation: OperationTypeDTO) -> PermissionNode:
        return PermissionNode(
            id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            entity_type=EntityType("vfolder"),
            permission=permission,
            operation=operation,
            created_at=datetime.now(tz=UTC),
        )

    def test_both_names_of_the_same_bit_are_carried(self) -> None:
        node = self._node(PermissionBitDTO.SOFT_DELETE, OperationTypeDTO.SOFT_DELETE)

        assert node.permission == PermissionBitDTO.SOFT_DELETE
        assert node.operation == OperationTypeDTO.SOFT_DELETE
        assert node.permission.value == "soft_delete"
        assert node.operation.value == "soft-delete"

    def test_the_bit_is_required(self) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            PermissionNode.model_validate({
                "id": str(uuid.uuid4()),
                "role_id": str(uuid.uuid4()),
                "entity_type": "vfolder",
                "operation": OperationTypeDTO.READ.value,
                "created_at": datetime.now(tz=UTC).isoformat(),
            })
