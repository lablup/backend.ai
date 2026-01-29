import uuid
from dataclasses import dataclass, field

from .id import ScopeId
from .permission import PermissionCreatorBeforePermissionGroupCreation, PermissionData


@dataclass
class PermissionGroupCreator:
    role_id: uuid.UUID
    scope_id: ScopeId
    permissions: list[PermissionCreatorBeforePermissionGroupCreation] = field(default_factory=list)


@dataclass
class PermissionGroupCreatorBeforeRoleCreation:
    scope_id: ScopeId
    permissions: list[PermissionCreatorBeforePermissionGroupCreation] = field(default_factory=list)

    def to_input(self, role_id: uuid.UUID) -> PermissionGroupCreator:
        return PermissionGroupCreator(
            role_id=role_id,
            scope_id=self.scope_id,
            permissions=self.permissions,
        )


@dataclass
class PermissionGroupData:
    id: uuid.UUID
    role_id: uuid.UUID
    scope_id: ScopeId


@dataclass
class PermissionGroupExtendedData:
    id: uuid.UUID
    role_id: uuid.UUID
    scope_id: ScopeId

    permissions: list[PermissionData]


@dataclass(frozen=True)
class PermissionGroupListResult:
    """Result of permission group search with pagination info."""

    items: list[PermissionGroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
