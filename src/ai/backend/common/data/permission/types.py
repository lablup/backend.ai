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


class OperationType(enum.StrEnum):
    """
    .. deprecated::
        Superseded by :class:`Permission`, an :class:`enum.IntFlag` bitmask.
        Retained because permission resolution and the ``permissions.operation``
        column still consume these string values; do not build new features on it.
    """

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    SOFT_DELETE = "soft-delete"
    HARD_DELETE = "hard-delete"
    GRANT_ALL = "grant:all"  # Allow user to grant all permissions, including grant of grant
    GRANT_READ = "grant:read"
    GRANT_UPDATE = "grant:update"
    GRANT_SOFT_DELETE = "grant:soft-delete"
    GRANT_HARD_DELETE = "grant:hard-delete"

    @classmethod
    def owner_operations(cls) -> set[OperationType]:
        """
        Returns a set of operations that are considered owner operations.
        Owner operations are those that allow full control over an entity.
        """
        return {op for op in cls}

    @classmethod
    def admin_operations(cls) -> set[OperationType]:
        """
        Returns a set of operations that are considered admin operations.
        Admin operations are those that allow management of entities, including creation and deletion.
        """
        return {op for op in cls}

    @classmethod
    def member_operations(cls) -> set[OperationType]:
        """
        Returns a set of operations that are considered member operations.
        Member operations are those that allow read access.
        """
        return {
            cls.READ,
        }


class FieldType(enum.StrEnum):
    """Field types for RBAC field-scoped entities.

    Deprecated: No longer actively used. The field-scoped entity concept
    (RBACFieldCreator/RBACFieldPurger) was removed by BEP-1048.
    Kept only for the existing entity_fields table schema compatibility.
    """

    KERNEL = "kernel"
    MODEL_REVISION = "model_revision"


GLOBAL_SCOPE_ID = "global"  # Deprecated: no longer used in RBAC scope hierarchy


def role_scope_types() -> tuple[EntityType, ...]:
    """The scopes a role is created in.

    A permission row names an entity type and no scope, so which entities a role may
    permit does not vary with the scope it sits in.
    """
    return (DomainEntityType(), ProjectEntityType(), UserEntityType())


_READ_ONLY_OPS: frozenset[OperationType] = frozenset({OperationType.READ})
_READ_AND_CREATE_OPS: frozenset[OperationType] = frozenset({
    OperationType.READ,
    OperationType.CREATE,
})


@functools.cache
def member_operations(entity_type: EntityType) -> frozenset[OperationType]:
    """Operations granted to a *member* role on the given entity type.

    Members of a project may create their own sessions, vfolders and deployments;
    on everything else a member reads.
    """
    creatable = {SessionEntityType(), VFolderEntityType(), DeploymentEntityType()}
    return _READ_AND_CREATE_OPS if entity_type in creatable else _READ_ONLY_OPS


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

    def to_operation(self) -> OperationType:
        """The :class:`OperationType` of a single-bit mask — the inverse of
        :meth:`from_operation` for the bits that have one."""
        match self:
            case Permission.READ:
                return OperationType.READ
            case Permission.UPDATE:
                return OperationType.UPDATE
            case Permission.CREATE:
                return OperationType.CREATE
            case Permission.SOFT_DELETE:
                return OperationType.SOFT_DELETE
            case Permission.HARD_DELETE:
                return OperationType.HARD_DELETE
            case _:
                raise ValueError(f"{self!r} is not a single operation bit")

    @classmethod
    def from_operation(cls, operation: OperationType) -> Permission:
        """Map a single :class:`OperationType` to its corresponding bit.

        Grant operations (``GRANT_*``) have no dedicated bit and map to
        :attr:`NONE`; grant authority is still carried by the legacy
        ``permissions.operation`` column during the transition.
        """
        match operation:
            case OperationType.READ:
                return cls.READ
            case OperationType.UPDATE:
                return cls.UPDATE
            case OperationType.CREATE:
                return cls.CREATE
            case OperationType.SOFT_DELETE:
                return cls.SOFT_DELETE
            case OperationType.HARD_DELETE:
                return cls.HARD_DELETE
            case _:
                return cls.NONE
