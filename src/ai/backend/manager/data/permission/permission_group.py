import uuid
from dataclasses import dataclass

from .id import ScopeId


@dataclass
class PermissionGroupCreator:
    role_id: uuid.UUID
    scope_id: ScopeId


@dataclass
class PermissionGroupCreatorBeforeRoleCreation:
    scope_id: ScopeId

    def to_input(self, role_id: uuid.UUID) -> PermissionGroupCreator:
        return PermissionGroupCreator(
            role_id=role_id,
            scope_id=self.scope_id,
        )


@dataclass
class PermissionGroupData:
    id: uuid.UUID
    role_id: uuid.UUID
    scope_id: ScopeId
