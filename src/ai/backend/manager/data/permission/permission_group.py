import uuid
from dataclasses import dataclass

from .id import ScopeId


@dataclass
class PermissionGroupCreator:
    role_id: uuid.UUID
    scope_id: ScopeId


@dataclass
class PermissionGroupData:
    id: uuid.UUID
    role_id: uuid.UUID
    scope_id: ScopeId
