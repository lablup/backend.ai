"""Common permission types shared between manager and client."""

from __future__ import annotations

import enum


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


class EntityType(enum.StrEnum):
    USER = "user"
    PROJECT = "project"
    DOMAIN = "domain"

    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"

    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact_registry"
    APP_CONFIG = "app_config"
    NOTIFICATION_CHANNEL = "notification_channel"
    NOTIFICATION_RULE = "notification_rule"
    MODEL_DEPLOYMENT = "model_deployment"

    @classmethod
    def _scope_types(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are considered scope types.
        """
        return {cls.USER, cls.PROJECT, cls.DOMAIN}

    @classmethod
    def _resource_types(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are considered resource types.
        """
        return {
            cls.VFOLDER,
            cls.IMAGE,
            cls.SESSION,
            cls.ARTIFACT,
            cls.ARTIFACT_REGISTRY,
            cls.APP_CONFIG,
            cls.NOTIFICATION_CHANNEL,
            cls.NOTIFICATION_RULE,
            cls.MODEL_DEPLOYMENT,
        }

    @classmethod
    def owner_accessible_entity_types_in_user(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are accessible by owner roles in user scope.
        """
        return cls._resource_types()

    @classmethod
    def admin_accessible_entity_types_in_project(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are accessible by admin roles.
        """
        return {*cls._resource_types(), cls.USER}

    @classmethod
    def admin_accessible_entity_types_in_domain(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are accessible by admin roles.
        """
        return {*cls._resource_types(), cls.USER}

    @classmethod
    def member_accessible_entity_types_in_project(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are accessible by member roles.
        """
        return {*cls._resource_types(), cls.USER}

    @classmethod
    def member_accessible_entity_types_in_domain(cls) -> set[EntityType]:
        """
        Returns a set of entity types that are accessible by member roles.
        """
        return {*cls._resource_types(), cls.USER}


class ScopeType(enum.StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    GLOBAL = "global"


GLOBAL_SCOPE_ID = "global"
