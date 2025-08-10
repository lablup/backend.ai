import enum

from ai.backend.manager.data.permission.types import (
    EntityType as OriginalEntityType,
)
from ai.backend.manager.data.permission.types import (
    OperationType as OriginalOperationType,
)
from ai.backend.manager.data.permission.types import (
    RoleSource as OriginalRoleSource,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as OriginalScopeType,
)


class RoleSource(enum.StrEnum):
    """
    Definition source of the role.
    """

    SYSTEM = "system"  # System-defined role, e.g., default roles
    CUSTOM = "custom"  # Custom role defined

    def to_original(self) -> OriginalRoleSource:
        return OriginalRoleSource(self.value)


class OperationType(enum.StrEnum):
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

    def to_original(self) -> OriginalOperationType:
        return OriginalOperationType(self.value)


OPERATIONS_FOR_SYSTEM_ROLE = tuple(op for op in OperationType)

OPERATIONS_FOR_CUSTOM_ROLE = (OperationType.READ,)


class ScopeType(enum.StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"

    def to_original(self) -> OriginalScopeType:
        return OriginalScopeType(self.value)


class EntityType(enum.StrEnum):
    USER = "user"
    PROJECT = "project"
    DOMAIN = "domain"

    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"

    def to_original(self) -> OriginalEntityType:
        return OriginalEntityType(self.value)
