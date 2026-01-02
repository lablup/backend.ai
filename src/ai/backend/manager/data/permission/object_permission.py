from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai.backend.manager.types import OptionalState

from .id import ObjectId
from .status import PermissionStatus
from .types import EntityType, OperationType


@dataclass
class ObjectPermissionCreateInputBeforeRoleCreation:
    """Input data for creating ObjectPermission before role is created.

    This is a plain data container. The conversion to CreatorSpec happens
    in the repository layer (db_source.py) to maintain proper dependency direction.
    """

    entity_type: EntityType
    entity_id: str
    operation: OperationType
    status: PermissionStatus = PermissionStatus.ACTIVE


@dataclass
class ObjectPermissionCreateInput:
    """Input data for creating ObjectPermission for an existing role.

    Used when adding object permissions to a role that already exists.
    """

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
    role_id: uuid.UUID
    object_id: ObjectId
    operation: OperationType
