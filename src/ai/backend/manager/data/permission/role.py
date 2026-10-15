from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import (
    EntityData,
    EntityIdentifier,
    EntityType,
    FieldData,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.common.types import SearchResult

from .permission import PermissionData
from .status import RoleStatus
from .types import (
    Permission,
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
    # The one scope the role belongs to.
    scope_type: EntityType
    scope_id: uuid.UUID
    auto_assign: bool = False
    description: str | None = None
    role_preset_id: RolePresetID | None = None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id


@dataclass(frozen=True)
class AssignedUserData(FieldData):
    """One row joining a user to a role they hold, a field row of the role."""

    id: uuid.UUID
    user_id: UserID
    role_id: RoleID
    granted_by: UserID | None
    granted_at: datetime


@dataclass(frozen=True)
class RoleDetailData:
    """
    Detailed information about a role.
    """

    id: uuid.UUID
    name: str
    source: RoleSource
    status: RoleStatus

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    scope_type: EntityType
    scope_id: uuid.UUID
    auto_assign: bool = False
    description: str | None = None
    role_preset_id: RolePresetID | None = None


@dataclass(frozen=True)
class UserRoleAssignmentInput:
    """
    Input to create a new user-role association.
    """

    user_id: UserID
    role_id: RoleID
    granted_by: UserID
    project_id: ProjectID | None = None


@dataclass(frozen=True)
class UserRoleRevocationInput:
    """
    Input to revoke a user-role association.
    """

    user_id: UserID
    role_id: RoleID


@dataclass(frozen=True)
class ProjectRoleCount:
    """Number of roles a user still holds in a project after revocation."""

    project_id: ProjectID
    remaining_count: int


@dataclass(frozen=True)
class RoleRevocationResult:
    """Result of revoking a role from a user."""

    revoked: AssignedUserData
    project_remaining_roles: list[ProjectRoleCount] = field(default_factory=list)


@dataclass(frozen=True)
class BulkRoleAssignmentFailure:
    """Failure information for a single user in bulk role assignment."""

    user_id: UserID
    message: str


@dataclass(frozen=True)
class BulkRoleAssignmentResultData:
    """Result of bulk role assignment."""

    successes: list[AssignedUserData] = field(default_factory=list)
    failures: list[BulkRoleAssignmentFailure] = field(default_factory=list)


@dataclass(frozen=True)
class BulkUserRoleRevocationInput:
    """Input for bulk revoking a role from multiple users."""

    role_id: RoleID
    user_ids: list[UserID]


@dataclass(frozen=True)
class BulkRoleRevocationFailure:
    """Failure information for a single user in bulk role revocation."""

    user_id: UserID
    message: str


@dataclass(frozen=True)
class BulkRoleRevocationResultData:
    """Result of bulk role revocation."""

    successes: list[AssignedUserData] = field(default_factory=list)
    failures: list[BulkRoleRevocationFailure] = field(default_factory=list)


@dataclass(frozen=True)
class BulkRolePermissionAddFailure:
    """Failure information for a single permission entry in bulk add (or replace)."""

    role_id: uuid.UUID
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
