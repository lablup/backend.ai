from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import (
    EntityData,
    EntityIdentifier,
    EntityType,
    ScopeType,
)
from ai.backend.manager.data.common.types import SearchResult

from .id import ObjectId, ScopeId
from .object_permission import (
    ObjectPermissionData,
)
from .permission import PermissionData
from .status import RoleStatus
from .types import (
    EntityType as LegacyEntityType,
)
from .types import (
    OperationType,
    Permission,
    RBACElementType,
    RoleSource,
)


@dataclass(frozen=True)
class RoleData(EntityData):
    """
    Information about a role.
    If detailed information is needed, use RoleDetailData.
    """

    id: RoleID
    name: str
    source: RoleSource
    status: RoleStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    auto_assign: bool = False
    description: str | None = None
    role_preset_id: RolePresetID | None = None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class AssignedUserData:
    """Information about a user assigned to a role."""

    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: uuid.UUID | None
    granted_at: datetime


@dataclass(frozen=True)
class RoleDetailData:
    """
    Detailed information about a role.
    It includes permission groups and object permissions.
    """

    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus

    object_permissions: list[ObjectPermissionData]

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    auto_assign: bool = False
    description: str | None = None
    role_preset_id: RolePresetID | None = None


@dataclass(frozen=True)
class ScopePermissionCheckInput:
    user_id: uuid.UUID
    target_entity_type: LegacyEntityType
    target_scope_id: ScopeId
    permission: Permission


@dataclass(frozen=True)
class SingleEntityPermissionCheckInput:
    user_id: uuid.UUID
    target_object_id: ObjectId
    operation: OperationType


@dataclass(frozen=True)
class BatchEntityPermissionCheckInput:
    user_id: uuid.UUID
    target_object_ids: list[ObjectId]
    operation: OperationType


@dataclass(frozen=True)
class PermissionResolutionKey:
    """Identifies a single (user, element_type, entity) target for permission resolution.

    A bulk permission resolver accepts a sequence of these keys and returns a
    mapping keyed by the same object, so each result is unambiguously tied to
    its input target.

    ``element_type`` controls scope-chain entry; ``subject_entity_type`` controls
    which ``permission.entity_type`` rows are matched. Callers that want the
    default mapping pass ``element_type`` itself.
    """

    user_id: uuid.UUID
    element_type: RBACElementType
    entity_id: str
    subject_entity_type: RBACElementType


@dataclass(frozen=True)
class ScopeChainPermissionCheckInput:
    key: PermissionResolutionKey
    permission: Permission


@dataclass(frozen=True)
class BulkPermissionCheckInput:
    keys: list[PermissionResolutionKey]
    permission: Permission


@dataclass(frozen=True)
class UserRoleAssignmentInput:
    """
    Input to create a new user-role association.
    """

    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


@dataclass(frozen=True)
class UserRoleAssignmentData:
    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: uuid.UUID | None = None


@dataclass(frozen=True)
class UserRoleRevocationInput:
    """
    Input to revoke a user-role association.
    """

    user_id: uuid.UUID
    role_id: uuid.UUID


@dataclass(frozen=True)
class ProjectRoleCount:
    """Number of roles a user still holds in a project after revocation."""

    project_id: uuid.UUID
    remaining_count: int


@dataclass(frozen=True)
class RoleRevocationResult:
    """Result of revoking a role from a user."""

    user_role_id: uuid.UUID
    project_remaining_roles: list[ProjectRoleCount] = field(default_factory=list)


@dataclass(frozen=True)
class UserRoleRevocationData:
    user_role_id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID


@dataclass(frozen=True)
class BulkUserRoleAssignmentInput:
    """Input for bulk assigning a role to multiple users."""

    role_id: uuid.UUID
    user_ids: list[uuid.UUID]
    granted_by: uuid.UUID | None = None


@dataclass(frozen=True)
class BulkRoleAssignmentFailure:
    """Failure information for a single user in bulk role assignment."""

    user_id: uuid.UUID
    message: str


@dataclass(frozen=True)
class BulkRoleAssignmentResultData:
    """Result of bulk role assignment."""

    successes: list[UserRoleAssignmentData] = field(default_factory=list)
    failures: list[BulkRoleAssignmentFailure] = field(default_factory=list)


@dataclass(frozen=True)
class BulkUserRoleRevocationInput:
    """Input for bulk revoking a role from multiple users."""

    role_id: uuid.UUID
    user_ids: list[uuid.UUID]


@dataclass(frozen=True)
class BulkRoleRevocationFailure:
    """Failure information for a single user in bulk role revocation."""

    user_id: uuid.UUID
    message: str


@dataclass(frozen=True)
class BulkRoleRevocationResultData:
    """Result of bulk role revocation."""

    successes: list[UserRoleRevocationData] = field(default_factory=list)
    failures: list[BulkRoleRevocationFailure] = field(default_factory=list)


@dataclass(frozen=True)
class BulkRolePermissionAddFailure:
    """Failure information for a single permission entry in bulk add (or replace)."""

    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    permission: Permission
    message: str


@dataclass(frozen=True)
class BulkRolePermissionAddResultData:
    """Result of bulk inserting role-permission rows."""

    successes: list[PermissionData] = field(default_factory=list)
    failures: list[BulkRolePermissionAddFailure] = field(default_factory=list)


@dataclass(frozen=True)
class BulkRolePermissionReplaceResultData:
    """Result of replacing a role's entire scoped-permission set."""

    role_id: uuid.UUID
    successes: list[PermissionData] = field(default_factory=list)
    failures: list[BulkRolePermissionAddFailure] = field(default_factory=list)


@dataclass(frozen=True)
class RoleListResult(SearchResult[RoleData]):
    """Result of role search with pagination info."""

    pass


@dataclass(frozen=True)
class AssignedUserListResult(SearchResult[AssignedUserData]):
    """Result of assigned user search with pagination info."""

    pass
