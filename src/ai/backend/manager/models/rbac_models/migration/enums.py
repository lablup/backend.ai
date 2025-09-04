import enum

from ai.backend.manager.data.permission.status import (
    RoleStatus as OriginalRoleStatus,
)
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


class RoleStatus(enum.StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

    def to_original(self) -> OriginalRoleStatus:
        return OriginalRoleStatus(self.value)


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

    @classmethod
    def owner_operations(cls) -> set["OperationType"]:
        """
        Returns a set of operations that are considered owner operations.
        Owner operations are those that allow full control over an entity.
        """
        return {op for op in cls}

    @classmethod
    def admin_operations(cls) -> set["OperationType"]:
        """
        Returns a set of operations that are considered admin operations.
        Admin operations are those that allow management of entities, including creation and deletion.
        """
        return {op for op in cls}

    @classmethod
    def member_operations(cls) -> set["OperationType"]:
        """
        Returns a set of operations that are considered member operations.
        Member operations are those that allow read access.
        """
        return {
            cls.READ,
        }


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

    @classmethod
    def _scope_types(cls) -> set["EntityType"]:
        """
        Returns a set of entity types that are considered scope types.
        """
        return {cls.USER, cls.PROJECT, cls.DOMAIN}

    @classmethod
    def _resource_types(cls) -> set["EntityType"]:
        """
        Returns a set of entity types that are considered resource types.
        """
        return {
            cls.VFOLDER,
            cls.IMAGE,
            cls.SESSION,
        }

    @classmethod
    def owner_accessible_entity_types_in_user(cls) -> set["EntityType"]:
        """
        Returns a set of entity types that are accessible by owner roles in user scope.
        """
        return cls._resource_types()

    @classmethod
    def admin_accessible_entity_types_in_project(cls) -> set["EntityType"]:
        """
        Returns a set of entity types that are accessible by admin roles.
        """
        return {*cls._resource_types(), cls.USER}

    @classmethod
    def member_accessible_entity_types_in_project(cls) -> set["EntityType"]:
        """
        Returns a set of entity types that are accessible by member roles.
        """
        return {*cls._resource_types(), cls.USER}
