import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.manager.types import OptionalState

from .id import ObjectId
from .status import PermissionStatus
from .types import EntityType, OperationType


@dataclass
class ObjectPermissionCreateInput:
    role_id: uuid.UUID
    entity_type: EntityType
    entity_id: str
    operation: OperationType
    status: PermissionStatus = PermissionStatus.ACTIVE


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
    status: PermissionStatus
    role_id: uuid.UUID
    object_id: ObjectId
    operation: OperationType
    created_at: datetime
