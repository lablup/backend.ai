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
    # === RBAC scope/resource types (original 12) ===
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

    # === Standalone entity types ===
    AGENT = "agent"
    AUTH = "auth"
    AUDIT_LOG = "audit_log"
    CONTAINER_METRIC = "container_metric"
    CONTAINER_METRIC_METADATA = "container_metric_metadata"
    CONTAINER_REGISTRY = "container_registry"
    DEPLOYMENT = "deployment"
    ERROR_LOG = "error_log"
    EXPORT = "export"
    GROUP = "group"
    MODEL_SERVICE = "model_service"
    NOTIFICATION = "notification"
    OBJECT_PERMISSION = "object_permission"
    ARTIFACT_STORAGE = "artifact_storage"
    OBJECT_STORAGE = "object_storage"
    PERMISSION = "permission"
    RESOURCE_GROUP = "resource_group"
    RESOURCE_PRESET = "resource_preset"
    ROLE = "role"
    STORAGE_NAMESPACE = "storage_namespace"
    VFS_STORAGE = "vfs_storage"

    # === Parent:child sub-entity types (`:` separator) ===
    # Domain/Project/User sub-resources
    DOMAIN_FAIR_SHARE = "domain:fair_share"
    PROJECT_FAIR_SHARE = "project:fair_share"
    USER_FAIR_SHARE = "user:fair_share"
    DOMAIN_USAGE_BUCKET = "domain:usage_bucket"
    PROJECT_USAGE_BUCKET = "project:usage_bucket"
    USER_USAGE_BUCKET = "user:usage_bucket"
    KEYPAIR_RESOURCE_POLICY = "keypair:resource_policy"
    PROJECT_RESOURCE_POLICY = "project:resource_policy"
    USER_RESOURCE_POLICY = "user:resource_policy"
    # App config sub
    APP_CONFIG_DOMAIN = "app_config:domain"
    APP_CONFIG_USER = "app_config:user"
    # Session sub
    SESSION_KERNEL = "session:kernel"
    SESSION_FILE = "session:file"
    SESSION_DIRECTORY = "session:directory"
    SESSION_APP_SERVICE = "session:app_service"
    SESSION_COMMIT = "session:commit"
    SESSION_STATUS_HISTORY = "session:status_history"
    SESSION_ABUSING_REPORT = "session:abusing_report"
    SESSION_CONTAINER_LOG = "session:container_log"
    SESSION_DEPENDENCY_GRAPH = "session:dependency_graph"
    SESSION_DIRECT_ACCESS = "session:direct_access"
    SESSION_HISTORY = "session:history"
    SESSION_SCOPED_HISTORY = "session:scoped_history"
    # Deployment sub
    DEPLOYMENT_REPLICA = "deployment:replica"
    DEPLOYMENT_ROUTE = "deployment:route"
    DEPLOYMENT_ACCESS_TOKEN = "deployment:access_token"
    DEPLOYMENT_AUTO_SCALING_RULE = "deployment:auto_scaling_rule"
    DEPLOYMENT_MODEL_REVISION = "deployment:model_revision"
    DEPLOYMENT_REVISION = "deployment:revision"
    DEPLOYMENT_POLICY = "deployment:policy"
    DEPLOYMENT_HISTORY = "deployment:history"
    DEPLOYMENT_SCOPED_HISTORY = "deployment:scoped_history"
    DEPLOYMENT_ERROR = "deployment:error"
    DEPLOYMENT_TOKEN = "deployment:token"
    # Image sub
    IMAGE_ALIAS = "image:alias"
    IMAGE_TAG = "image:tag"
    IMAGE_PRELOAD = "image:preload"
    IMAGE_SCAN = "image:scan"
    IMAGE_AGENT = "image:agent"
    IMAGE_RESOURCE_LIMIT = "image:resource_limit"
    # Artifact sub
    ARTIFACT_REVISION = "artifact:revision"
    ARTIFACT_SCAN = "artifact:scan"
    ARTIFACT_MODEL = "artifact:model"
    ARTIFACT_IMPORT = "artifact:import"
    ARTIFACT_DOWNLOAD = "artifact:download"
    ARTIFACT_README = "artifact:readme"
    ARTIFACT_VERIFICATION = "artifact:verification"
    ARTIFACT_REVISION_STORAGE_LINK = "artifact:revision:storage_link"
    # VFolder sub
    VFOLDER_FILE = "vfolder:file"
    VFOLDER_DIRECTORY = "vfolder:directory"
    VFOLDER_INVITATION = "vfolder:invitation"
    # Resource group sub
    RESOURCE_GROUP_DOMAIN = "resource_group:domain"
    RESOURCE_GROUP_KEYPAIR = "resource_group:keypair"
    RESOURCE_GROUP_USER_GROUP = "resource_group:user_group"
    RESOURCE_GROUP_FAIR_SHARE = "resource_group:fair_share"
    RESOURCE_GROUP_RESOURCE = "resource_group:resource"
    # Role sub
    ROLE_ASSIGNMENT = "role:assignment"
    ROLE_USER = "role:user"
    ROLE_ENTITY = "role:entity"
    ROLE_SCOPE = "role:scope"
    ROLE_PERMISSION = "role:permission"
    ROLE_ENTITY_TYPE = "role:entity_type"
    ROLE_SCOPE_TYPE = "role:scope_type"
    # Container registry sub
    CONTAINER_REGISTRY_IMAGE = "container_registry:image"
    # Route sub
    ROUTE_HISTORY = "route:history"
    ROUTE_SCOPED_HISTORY = "route:scoped_history"
    # Auth sub
    AUTH_TOKEN = "auth:token"
    AUTH_ACCOUNT = "auth:account"
    AUTH_SESSION = "auth:session"
    AUTH_PASSWORD = "auth:password"
    AUTH_PROFILE = "auth:profile"
    AUTH_SSH_KEYPAIR = "auth:ssh_keypair"
    # Notification sub
    NOTIFICATION_EVENT = "notification:event"
    NOTIFICATION_CHANNEL_VALIDATION = "notification:channel_validation"
    NOTIFICATION_RULE_VALIDATION = "notification:rule_validation"
    # Group sub
    GROUP_USAGE = "group:usage"
    # User sub
    USER_STATS = "user:stats"
    # Agent sub
    AGENT_WATCHER = "agent:watcher"
    AGENT_REGISTRY = "agent:registry"
    # Resource preset sub
    RESOURCE_PRESET_CHECK = "resource_preset:check"
    # Permission sub
    PERMISSION_CHECK = "permission:check"
    # Export sub
    EXPORT_REPORT = "export:report"

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


class FieldType(enum.StrEnum):
    """Field types for RBAC field-scoped entities.

    Fields are sub-resources that belong to a parent entity.
    Unlike EntityType which represents scope-scoped entities,
    FieldType represents entity-scoped sub-entities.
    """

    KERNEL = "kernel"
    MODEL_REVISION = "model_revision"


class ScopeType(enum.StrEnum):
    # === Organization/permission scopes (original) ===
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    GLOBAL = "global"

    RESOURCE_GROUP = "resource_group"
    CONTAINER_REGISTRY = "container_registry"
    ARTIFACT_REGISTRY = "artifact_registry"
    STORAGE_HOST = "storage_host"

    # === Entity-level scopes ===
    SESSION = "session"
    DEPLOYMENT = "deployment"
    VFOLDER = "vfolder"
    IMAGE = "image"
    ARTIFACT = "artifact"
    ARTIFACT_REVISION = "artifact_revision"
    ROLE = "role"


GLOBAL_SCOPE_ID = "global"


class RelationType(enum.StrEnum):
    """Classification of parent-child entity edges in BEP-1048.

    AUTO: Composition edge with permission delegation from parent.
    REF: Read-only reference edge with no permission delegation.
    """

    AUTO = "auto"
    REF = "ref"
