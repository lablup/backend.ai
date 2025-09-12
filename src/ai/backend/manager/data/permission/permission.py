import uuid
from dataclasses import dataclass

from .types import EntityType, OperationType


@dataclass
class PermissionCreator:
    permission_group_id: uuid.UUID
    entity_type: EntityType
    operation: OperationType


@dataclass
class PermissionData:
    id: uuid.UUID
    permission_group_id: uuid.UUID
    entity_type: EntityType
    operation: OperationType
