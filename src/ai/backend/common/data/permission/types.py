"""Common permission types shared between manager and client."""

from __future__ import annotations

import enum
import functools

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType


class PermissionStatus(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' status is used when the permission is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' status is used when the permission is permanently removed
    DELETED = "deleted"


class RoleStatus(enum.StrEnum):
    """Status of a role."""

    ACTIVE = "active"
    # 'inactive' status is used when the role is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' status is used when the role is permanently removed
    DELETED = "deleted"


class RoleSource(enum.StrEnum):
    """Definition source of the role."""

    SYSTEM = "system"  # System-defined role, e.g., default roles
    CUSTOM = "custom"  # Custom role defined


GLOBAL_SCOPE_ID = "global"  # Deprecated: no longer used in RBAC scope hierarchy


def role_scope_types() -> tuple[EntityType, ...]:
    """The scopes a role is created in.

    A permission row names an entity type and no scope, so which entities a role may
    permit does not vary with the scope it sits in.
    """
    return (DomainEntityType(), ProjectEntityType(), UserEntityType())


class Permission(enum.IntFlag):
    """A bitmask of operations, each a distinct power-of-two bit.

    Bit magnitude carries no semantics; checks are purely bitwise:

    * does the mask include an operation?  ``bool(mask & Permission.X)``
    * is one mask a subset of another?     ``(a & ~b) == Permission.NONE``
    * intersect / union two masks          ``a & b`` / ``a | b``
    """

    NONE = 0
    READ = 1 << 0
    UPDATE = 1 << 1
    CREATE = 1 << 2
    SOFT_DELETE = 1 << 3
    HARD_DELETE = 1 << 4

    @classmethod
    def full(cls) -> Permission:
        """The full permission cap — every operation allowed."""
        return cls.READ | cls.UPDATE | cls.CREATE | cls.SOFT_DELETE | cls.HARD_DELETE

    @classmethod
    def field_bearing(cls) -> Permission:
        """The operations that state a field scope — read and update."""
        return cls.READ | cls.UPDATE

    def covers(self, required: Permission) -> bool:
        """Whether this mask holds *every* bit of ``required``.

        A requirement may be a mask rather than a single bit (``UPSERT`` requires
        ``CREATE | UPDATE``), so holding any one of its bits is not enough.
        """
        return (required & ~self) == Permission.NONE


_READ_ONLY: Permission = Permission.READ
_READ_AND_CREATE: Permission = Permission.READ | Permission.CREATE


@functools.cache
def member_permissions(entity_type: EntityType) -> Permission:
    """The permission a *member* role holds on the given entity type.

    Members of a project may create their own sessions, vfolders and deployments;
    on everything else a member reads.
    """
    creatable = {SessionEntityType(), VFolderEntityType(), DeploymentEntityType()}
    return _READ_AND_CREATE if entity_type in creatable else _READ_ONLY
