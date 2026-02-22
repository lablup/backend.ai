"""Common permission types shared between manager and client."""

from __future__ import annotations

import enum
from typing import Final

from ai.backend.common.data.permission.exceptions import InvalidTypeConversionError


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
    OBJECT_STORAGE = "object_storage"
    PERMISSION = "permission"
    RESOURCE_GROUP = "resource_group"
    RESOURCE_PRESET = "resource_preset"
    ROLE = "role"
    STORAGE_HOST = "storage_host"
    STORAGE_NAMESPACE = "storage_namespace"
    VFS_STORAGE = "vfs_storage"
    KEYPAIR = "keypair"
    NETWORK = "network"

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
    KERNEL_SCHEDULING_HISTORY = "session:kernel:scheduling_history"
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
    DEPLOYMENT_AUTO_SCALING_POLICY = "deployment:auto_scaling_policy"
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
    VFOLDER_PERMISSION = "vfolder:permission"
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
    USER_ROLE = "user:role"
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

    def to_element(self) -> RBACElementType:
        from ai.backend.common.exception import RBACTypeConversionError

        try:
            return RBACElementType(self.value)
        except ValueError as e:
            raise RBACTypeConversionError(f"{self!r} has no corresponding RBACElementType") from e


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

    def to_element(self) -> RBACElementType:
        from ai.backend.common.exception import RBACTypeConversionError

        try:
            return RBACElementType(self.value)
        except ValueError as e:
            raise RBACTypeConversionError(f"{self!r} has no corresponding RBACElementType") from e


GLOBAL_SCOPE_ID = "global"


class RBACElementType(enum.StrEnum):
    """Unified element type for the RBAC scope-entity relationship model.

    Each value identifies an element in the RBAC permission hierarchy
    that can act as a scope (parent) or an entity (child) depending on
    the relationship direction.

    This enum replaces the separate ``ScopeType`` and RBAC-subset of
    ``EntityType`` with a single unified type.
    """

    # === Scope hierarchy ===
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"

    # === Root-query-enabled entities (scoped) ===
    SESSION = "session"
    VFOLDER = "vfolder"
    DEPLOYMENT = "deployment"
    MODEL_DEPLOYMENT = "model_deployment"
    KEYPAIR = "keypair"
    NOTIFICATION_CHANNEL = "notification_channel"
    NETWORK = "network"
    RESOURCE_GROUP = "resource_group"
    CONTAINER_REGISTRY = "container_registry"
    STORAGE_HOST = "storage_host"
    IMAGE = "image"
    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact_registry"
    SESSION_TEMPLATE = "session_template"
    APP_CONFIG = "app_config"

    # === Root-query-enabled entities (superadmin-only) ===
    RESOURCE_PRESET = "resource_preset"
    USER_RESOURCE_POLICY = "user_resource_policy"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    EVENT_LOG = "event_log"

    # === Auto-only entities used in permissions ===
    NOTIFICATION_RULE = "notification_rule"

    # === Entity-level scopes (for entity-scope permissions) ===
    ARTIFACT_REVISION = "artifact_revision"

    def to_scope_type(self) -> ScopeType:
        """Temporary bridge for DB/ORM layers that still use ScopeType.

        TODO: Remove after the RBAC ORM migration and ScopeType removal are complete.
        """
        from ai.backend.common.exception import RBACTypeConversionError

        try:
            return ScopeType(self.value)
        except ValueError as e:
            raise RBACTypeConversionError(f"{self!r} has no corresponding ScopeType") from e

    def to_entity_type(self) -> EntityType:
        """Temporary bridge for DB/ORM layers that still use EntityType.

        TODO: Remove after the RBAC ORM migration and EntityType RBAC usage removal are complete.
        """
        from ai.backend.common.exception import RBACTypeConversionError

        try:
            return EntityType(self.value)
        except ValueError as e:
            raise RBACTypeConversionError(f"{self!r} has no corresponding EntityType") from e


class RelationType(enum.StrEnum):
    """Classification of parent-child entity edges in BEP-1048.

    AUTO: Composition edge with permission delegation from parent.
    REF: Read-only reference edge with no permission delegation.
    """

    AUTO = "auto"
    REF = "ref"


def _get_entity_children(parent: EntityType) -> dict[EntityType, RelationType]:
    """Return the children of a parent entity type with their relation types.

    Every EntityType value must have an explicit case to ensure exhaustive coverage.
    """
    match parent:
        # --- Parents with children ---
        case EntityType.SESSION:
            return {
                EntityType.SESSION_KERNEL: RelationType.AUTO,
                EntityType.DEPLOYMENT_ROUTE: RelationType.AUTO,
                EntityType.SESSION_DEPENDENCY_GRAPH: RelationType.AUTO,
                EntityType.SESSION_STATUS_HISTORY: RelationType.AUTO,
                EntityType.AGENT: RelationType.REF,
                EntityType.RESOURCE_GROUP: RelationType.REF,
                EntityType.KEYPAIR: RelationType.REF,
            }
        case EntityType.RESOURCE_GROUP:
            return {
                EntityType.AGENT: RelationType.AUTO,
                EntityType.DOMAIN_FAIR_SHARE: RelationType.AUTO,
                EntityType.PROJECT_FAIR_SHARE: RelationType.AUTO,
                EntityType.USER_FAIR_SHARE: RelationType.AUTO,
            }
        case EntityType.AGENT:
            return {
                EntityType.SESSION_KERNEL: RelationType.AUTO,
            }
        case EntityType.CONTAINER_REGISTRY:
            return {
                EntityType.IMAGE: RelationType.AUTO,
            }
        case EntityType.IMAGE:
            return {
                EntityType.IMAGE_ALIAS: RelationType.AUTO,
            }
        case EntityType.VFOLDER:
            return {
                EntityType.VFOLDER_PERMISSION: RelationType.AUTO,
                EntityType.VFOLDER_INVITATION: RelationType.AUTO,
            }
        case EntityType.MODEL_DEPLOYMENT:
            return {
                EntityType.DEPLOYMENT_TOKEN: RelationType.AUTO,
                EntityType.DEPLOYMENT_AUTO_SCALING_RULE: RelationType.AUTO,
                EntityType.DEPLOYMENT_REVISION: RelationType.AUTO,
                EntityType.DEPLOYMENT_POLICY: RelationType.AUTO,
                EntityType.DEPLOYMENT_AUTO_SCALING_POLICY: RelationType.AUTO,
                EntityType.DEPLOYMENT_HISTORY: RelationType.AUTO,
                EntityType.DEPLOYMENT_ROUTE: RelationType.AUTO,
                EntityType.IMAGE: RelationType.REF,
                EntityType.USER: RelationType.REF,
            }
        case EntityType.ARTIFACT:
            return {
                EntityType.ARTIFACT_REVISION: RelationType.AUTO,
                EntityType.ARTIFACT_REGISTRY: RelationType.REF,
            }
        case EntityType.NOTIFICATION_CHANNEL:
            return {
                EntityType.NOTIFICATION_RULE: RelationType.AUTO,
                EntityType.USER: RelationType.REF,
            }
        case EntityType.SESSION_KERNEL:
            return {
                EntityType.KERNEL_SCHEDULING_HISTORY: RelationType.AUTO,
                EntityType.IMAGE: RelationType.REF,
                EntityType.AGENT: RelationType.REF,
            }
        case EntityType.DEPLOYMENT_ROUTE:
            return {
                EntityType.ROUTE_HISTORY: RelationType.AUTO,
                EntityType.MODEL_DEPLOYMENT: RelationType.REF,
                EntityType.SESSION: RelationType.REF,
            }
        case EntityType.DOMAIN:
            return {
                EntityType.DOMAIN_FAIR_SHARE: RelationType.AUTO,
            }
        case EntityType.PROJECT:
            return {
                EntityType.PROJECT_FAIR_SHARE: RelationType.AUTO,
                EntityType.SESSION: RelationType.AUTO,
                EntityType.PROJECT_RESOURCE_POLICY: RelationType.REF,
            }
        case EntityType.USER:
            return {
                EntityType.USER_FAIR_SHARE: RelationType.AUTO,
                EntityType.USER_RESOURCE_POLICY: RelationType.REF,
                EntityType.KEYPAIR: RelationType.REF,
            }
        case EntityType.ROLE:
            return {
                EntityType.PERMISSION: RelationType.AUTO,
                EntityType.USER_ROLE: RelationType.AUTO,
            }
        case EntityType.VFOLDER_PERMISSION:
            return {
                EntityType.USER: RelationType.REF,
            }
        case EntityType.VFOLDER_INVITATION:
            return {
                EntityType.USER: RelationType.REF,
            }
        case EntityType.KEYPAIR:
            return {
                EntityType.KEYPAIR_RESOURCE_POLICY: RelationType.REF,
                EntityType.USER: RelationType.REF,
            }
        case EntityType.NETWORK:
            return {
                EntityType.DOMAIN: RelationType.REF,
                EntityType.PROJECT: RelationType.REF,
            }
        case EntityType.USER_ROLE:
            return {
                EntityType.USER: RelationType.REF,
            }
        case EntityType.NOTIFICATION_RULE:
            return {
                EntityType.USER: RelationType.REF,
            }
        # --- Leaf nodes (no children) ---
        case EntityType.AUTH:
            return {}
        case EntityType.AUDIT_LOG:
            return {}
        case EntityType.CONTAINER_METRIC:
            return {}
        case EntityType.CONTAINER_METRIC_METADATA:
            return {}
        case EntityType.DEPLOYMENT:
            return {}
        case EntityType.ERROR_LOG:
            return {}
        case EntityType.EXPORT:
            return {}
        case EntityType.GROUP:
            return {}
        case EntityType.MODEL_SERVICE:
            return {}
        case EntityType.NOTIFICATION:
            return {}
        case EntityType.OBJECT_PERMISSION:
            return {}
        case EntityType.OBJECT_STORAGE:
            return {}
        case EntityType.PERMISSION:
            return {}
        case EntityType.RESOURCE_PRESET:
            return {}
        case EntityType.STORAGE_HOST:
            return {}
        case EntityType.STORAGE_NAMESPACE:
            return {}
        case EntityType.VFS_STORAGE:
            return {}
        case EntityType.ARTIFACT_REGISTRY:
            return {}
        case EntityType.APP_CONFIG:
            return {}
        case EntityType.DOMAIN_FAIR_SHARE:
            return {}
        case EntityType.PROJECT_FAIR_SHARE:
            return {}
        case EntityType.USER_FAIR_SHARE:
            return {}
        case EntityType.DOMAIN_USAGE_BUCKET:
            return {}
        case EntityType.PROJECT_USAGE_BUCKET:
            return {}
        case EntityType.USER_USAGE_BUCKET:
            return {}
        case EntityType.KEYPAIR_RESOURCE_POLICY:
            return {}
        case EntityType.PROJECT_RESOURCE_POLICY:
            return {}
        case EntityType.USER_RESOURCE_POLICY:
            return {}
        case EntityType.APP_CONFIG_DOMAIN:
            return {}
        case EntityType.APP_CONFIG_USER:
            return {}
        case EntityType.KERNEL_SCHEDULING_HISTORY:
            return {}
        case EntityType.SESSION_FILE:
            return {}
        case EntityType.SESSION_DIRECTORY:
            return {}
        case EntityType.SESSION_APP_SERVICE:
            return {}
        case EntityType.SESSION_COMMIT:
            return {}
        case EntityType.SESSION_STATUS_HISTORY:
            return {}
        case EntityType.SESSION_ABUSING_REPORT:
            return {}
        case EntityType.SESSION_CONTAINER_LOG:
            return {}
        case EntityType.SESSION_DEPENDENCY_GRAPH:
            return {}
        case EntityType.SESSION_DIRECT_ACCESS:
            return {}
        case EntityType.SESSION_HISTORY:
            return {}
        case EntityType.SESSION_SCOPED_HISTORY:
            return {}
        case EntityType.DEPLOYMENT_REPLICA:
            return {}
        case EntityType.DEPLOYMENT_ACCESS_TOKEN:
            return {}
        case EntityType.DEPLOYMENT_AUTO_SCALING_RULE:
            return {}
        case EntityType.DEPLOYMENT_MODEL_REVISION:
            return {}
        case EntityType.DEPLOYMENT_REVISION:
            return {}
        case EntityType.DEPLOYMENT_POLICY:
            return {}
        case EntityType.DEPLOYMENT_HISTORY:
            return {}
        case EntityType.DEPLOYMENT_SCOPED_HISTORY:
            return {}
        case EntityType.DEPLOYMENT_ERROR:
            return {}
        case EntityType.DEPLOYMENT_TOKEN:
            return {}
        case EntityType.DEPLOYMENT_AUTO_SCALING_POLICY:
            return {}
        case EntityType.IMAGE_ALIAS:
            return {}
        case EntityType.IMAGE_TAG:
            return {}
        case EntityType.IMAGE_PRELOAD:
            return {}
        case EntityType.IMAGE_SCAN:
            return {}
        case EntityType.IMAGE_AGENT:
            return {}
        case EntityType.IMAGE_RESOURCE_LIMIT:
            return {}
        case EntityType.ARTIFACT_REVISION:
            return {}
        case EntityType.ARTIFACT_SCAN:
            return {}
        case EntityType.ARTIFACT_MODEL:
            return {}
        case EntityType.ARTIFACT_IMPORT:
            return {}
        case EntityType.ARTIFACT_DOWNLOAD:
            return {}
        case EntityType.ARTIFACT_README:
            return {}
        case EntityType.ARTIFACT_VERIFICATION:
            return {}
        case EntityType.ARTIFACT_REVISION_STORAGE_LINK:
            return {}
        case EntityType.VFOLDER_FILE:
            return {}
        case EntityType.VFOLDER_DIRECTORY:
            return {}
        case EntityType.RESOURCE_GROUP_DOMAIN:
            return {}
        case EntityType.RESOURCE_GROUP_KEYPAIR:
            return {}
        case EntityType.RESOURCE_GROUP_USER_GROUP:
            return {}
        case EntityType.RESOURCE_GROUP_FAIR_SHARE:
            return {}
        case EntityType.RESOURCE_GROUP_RESOURCE:
            return {}
        case EntityType.ROLE_ASSIGNMENT:
            return {}
        case EntityType.ROLE_USER:
            return {}
        case EntityType.ROLE_ENTITY:
            return {}
        case EntityType.ROLE_SCOPE:
            return {}
        case EntityType.ROLE_PERMISSION:
            return {}
        case EntityType.ROLE_ENTITY_TYPE:
            return {}
        case EntityType.ROLE_SCOPE_TYPE:
            return {}
        case EntityType.CONTAINER_REGISTRY_IMAGE:
            return {}
        case EntityType.ROUTE_HISTORY:
            return {}
        case EntityType.ROUTE_SCOPED_HISTORY:
            return {}
        case EntityType.AUTH_TOKEN:
            return {}
        case EntityType.AUTH_ACCOUNT:
            return {}
        case EntityType.AUTH_SESSION:
            return {}
        case EntityType.AUTH_PASSWORD:
            return {}
        case EntityType.AUTH_PROFILE:
            return {}
        case EntityType.AUTH_SSH_KEYPAIR:
            return {}
        case EntityType.NOTIFICATION_EVENT:
            return {}
        case EntityType.NOTIFICATION_CHANNEL_VALIDATION:
            return {}
        case EntityType.NOTIFICATION_RULE_VALIDATION:
            return {}
        case EntityType.GROUP_USAGE:
            return {}
        case EntityType.USER_STATS:
            return {}
        case EntityType.AGENT_WATCHER:
            return {}
        case EntityType.AGENT_REGISTRY:
            return {}
        case EntityType.RESOURCE_PRESET_CHECK:
            return {}
        case EntityType.PERMISSION_CHECK:
            return {}
        case EntityType.EXPORT_REPORT:
            return {}


ENTITY_GRAPH: Final[dict[EntityType, dict[EntityType, RelationType]]] = {
    entity_type: _get_entity_children(entity_type) for entity_type in EntityType
}


def get_relation_type(parent: EntityType, child: EntityType) -> RelationType | None:
    return ENTITY_GRAPH.get(parent, {}).get(child)


def scope_type_to_entity_type(scope_type: ScopeType) -> EntityType:
    """Convert a ScopeType to its corresponding EntityType.

    Raises InvalidTypeConversionError for ScopeType.GLOBAL which has no entity mapping.
    """
    match scope_type:
        case ScopeType.GLOBAL:
            raise InvalidTypeConversionError("ScopeType.GLOBAL has no corresponding EntityType")
        case ScopeType.DOMAIN:
            return EntityType.DOMAIN
        case ScopeType.PROJECT:
            return EntityType.PROJECT
        case ScopeType.USER:
            return EntityType.USER
        case ScopeType.RESOURCE_GROUP:
            return EntityType.RESOURCE_GROUP
        case ScopeType.CONTAINER_REGISTRY:
            return EntityType.CONTAINER_REGISTRY
        case ScopeType.ARTIFACT_REGISTRY:
            return EntityType.ARTIFACT_REGISTRY
        case ScopeType.STORAGE_HOST:
            return EntityType.STORAGE_HOST
        case ScopeType.SESSION:
            return EntityType.SESSION
        case ScopeType.DEPLOYMENT:
            return EntityType.DEPLOYMENT
        case ScopeType.VFOLDER:
            return EntityType.VFOLDER
        case ScopeType.IMAGE:
            return EntityType.IMAGE
        case ScopeType.ARTIFACT:
            return EntityType.ARTIFACT
        case ScopeType.ARTIFACT_REVISION:
            return EntityType.ARTIFACT_REVISION
        case ScopeType.ROLE:
            return EntityType.ROLE


SCOPE_TO_ENTITY_MAP: Final[dict[ScopeType, EntityType]] = {
    scope_type: scope_type_to_entity_type(scope_type)
    for scope_type in ScopeType
    if scope_type != ScopeType.GLOBAL
}

ENTITY_TO_SCOPE_MAP: Final[dict[EntityType, ScopeType]] = {
    entity_type: scope_type for scope_type, entity_type in SCOPE_TO_ENTITY_MAP.items()
}


def entity_type_to_scope_type(entity_type: EntityType) -> ScopeType:
    """Convert an EntityType to its corresponding ScopeType.

    Raises InvalidTypeConversionError if the entity type has no scope mapping.
    """
    try:
        return ENTITY_TO_SCOPE_MAP[entity_type]
    except KeyError as e:
        raise InvalidTypeConversionError(f"{entity_type!r} has no corresponding ScopeType") from e
