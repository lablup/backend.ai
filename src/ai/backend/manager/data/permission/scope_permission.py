import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.manager.types import OptionalState

from .id import ObjectId, ScopeId
from .status import PermissionStatus
from .types import EntityType, ScopeType


@dataclass
class ScopePermissionCreateInput:
    role_id: uuid.UUID
    entity_type: str
    operation: str
    scope_type: ScopeType
    scope_id: str
    status: PermissionStatus = PermissionStatus.ACTIVE


@dataclass
class ScopePermissionUpdater:
    id: uuid.UUID
    status: OptionalState[PermissionStatus]


@dataclass
class ScopePermissionDeleteInput:
    id: uuid.UUID
    _status: PermissionStatus = PermissionStatus.DELETED


@dataclass
class ScopePermissionData:
    id: uuid.UUID
    status: PermissionStatus
    role_id: uuid.UUID
    entity_type: EntityType
    operation: str
    scope_id: ScopeId
    created_at: datetime


@dataclass
class ScopePermissionDataWithEntity:
    id: uuid.UUID
    status: PermissionStatus
    role_id: uuid.UUID
    entity_type: EntityType
    operation: str
    scope_id: ScopeId
    created_at: datetime

    mapped_entities: list[ObjectId]
