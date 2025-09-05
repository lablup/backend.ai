import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.types import Creator, OptionalState

from .id import ObjectId
from .status import PermissionStatus
from .types import EntityType, OperationType


@dataclass
class ObjectPermissionCreateInput(Creator):
    role_id: uuid.UUID
    entity_type: EntityType
    entity_id: str
    operation: OperationType
    status: PermissionStatus = PermissionStatus.ACTIVE

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "status": self.status,
        }


@dataclass
class ObjectPermissionCreateInputBeforeRoleCreation:
    entity_type: EntityType
    entity_id: str
    operation: OperationType
    status: PermissionStatus = PermissionStatus.ACTIVE

    def to_input(self, role_id: uuid.UUID) -> ObjectPermissionCreateInput:
        return ObjectPermissionCreateInput(
            role_id=role_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            operation=self.operation,
            status=self.status,
        )


@dataclass
class ObjectPermissionUpdater:
    id: uuid.UUID
    status: OptionalState[PermissionStatus]


@dataclass
class ObjectPermissionDeleteInput:
    id: uuid.UUID
    _status: PermissionStatus = PermissionStatus.DELETED


@dataclass
class ObjectPermissionData:
    id: uuid.UUID
    role_id: uuid.UUID
    object_id: ObjectId
    operation: OperationType
