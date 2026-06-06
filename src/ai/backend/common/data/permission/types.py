"""Common permission types shared between manager and client."""

from __future__ import annotations

import enum
import functools
from collections.abc import Mapping


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


class EntityType(enum.StrEnum):
    """
    Deprecated for RBAC: use ``RBACElementType`` instead
    or use ai.backend.common.entity.types.EntityType for non-RBAC-specific contexts.
    """

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
    PROJECT_ADMIN_PAGE = "project_admin_page"
    DOMAIN_ADMIN_PAGE = "domain_admin_page"
    SERVICE_CATALOG = "service_catalog"
    AUDIT_LOG = "audit_log"
    CONTAINER_METRIC = "container_metric"
    CONTAINER_METRIC_METADATA = "container_metric_metadata"
    CONTAINER_LIVE_STAT = "container_live_stat"
    CONTAINER_REGISTRY = "container_registry"
    DEPLOYMENT = "deployment"
    ERROR_LOG = "error_log"
    EXPORT = "export"
    GROUP = "group"
    KERNEL = "kernel"
    KEYPAIR = "keypair"
    LOGIN_CLIENT_TYPE = "login_client_type"
    LOGIN_SESSION = "login_session"
    MODEL_SERVICE = "model_service"
    NETWORK = "network"
    NOTIFICATION = "notification"
    OBJECT_PERMISSION = "object_permission"
    OBJECT_STORAGE = "object_storage"
    PERMISSION = "permission"
    AGENT_RESOURCE = "agent_resource"
    RESOURCE_ALLOCATION = "resource_allocation"
    RESOURCE_SLOT_TYPE = "resource_slot_type"
    RESOURCE_OVERVIEW = "resource_overview"
    RESOURCE_GROUP = "resource_group"
    PROMETHEUS_QUERY_PRESET = "prometheus_query_preset"
    PROMETHEUS_QUERY_PRESET_CATEGORY = "prometheus_query_preset_category"
    RESOURCE_PRESET = "resource_preset"
    MODEL_CARD = "model_card"
    ROLE = "role"
    RUNTIME_VARIANT = "runtime_variant"
    ROUTING = "routing"
    DOTFILE = "dotfile"
    ETCD_CONFIG = "etcd_config"
    MANAGER_ADMIN = "manager_admin"
    SESSION_TEMPLATE = "session_template"
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
    ARTIFACT_REVISION = "artifact_revision"
    ARTIFACT_SCAN = "artifact:scan"
    ARTIFACT_MODEL = "artifact:model"
    ARTIFACT_IMPORT = "artifact:import"
    ARTIFACT_DOWNLOAD = "artifact:download"
    ARTIFACT_README = "artifact:readme"
    ARTIFACT_VERIFICATION = "artifact:verification"
    ARTIFACT_REVISION_STORAGE_LINK = "artifact_revision:storage_link"
    # VFolder sub
    VFOLDER_FILE = "vfolder:file"
    VFOLDER_DIRECTORY = "vfolder:directory"
    VFOLDER_INVITATION = "vfolder:invitation"
    VFOLDER_DATA = "vfolder:data"
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
    USER_EMAIL = "user:email"
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
            cls.MODEL_CARD,
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

    Deprecated: No longer actively used. The field-scoped entity concept
    (RBACFieldCreator/RBACFieldPurger) was removed by BEP-1048.
    Kept only for the existing entity_fields table schema compatibility.
    """

    KERNEL = "kernel"
    MODEL_REVISION = "model_revision"


class ScopeType(enum.StrEnum):
    """Deprecated for RBAC: use ``RBACElementType`` instead."""

    # === Organization/permission scopes (original) ===
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    GLOBAL = "global"  # Deprecated: no longer used in RBAC scope hierarchy

    RESOURCE_GROUP = "resource_group"
    CONTAINER_REGISTRY = "container_registry"
    ARTIFACT_REGISTRY = "artifact_registry"
    STORAGE_HOST = "storage_host"

    # === Entity-level scopes ===
    SESSION = "session"
    DEPLOYMENT = "deployment"
    MODEL_DEPLOYMENT = "model_deployment"
    VFOLDER = "vfolder"
    IMAGE = "image"
    ARTIFACT = "artifact"
    ARTIFACT_REVISION = "artifact_revision"
    AGENT = "agent"
    ROLE = "role"
    ROLE_ASSIGNMENT = "role:assignment"
    NOTIFICATION_CHANNEL = "notification_channel"
    KEYPAIR = "keypair"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"

    def to_element(self) -> RBACElementType:
        from ai.backend.common.exception import RBACTypeConversionError

        try:
            return RBACElementType(self.value)
        except ValueError as e:
            raise RBACTypeConversionError(f"{self!r} has no corresponding RBACElementType") from e


GLOBAL_SCOPE_ID = "global"  # Deprecated: no longer used in RBAC scope hierarchy


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
    MODEL_DEPLOYMENT = "model_deployment"
    KEYPAIR = "keypair"
    NOTIFICATION_CHANNEL = "notification_channel"
    NETWORK = "network"
    RESOURCE_GROUP = "resource_group"
    CONTAINER_REGISTRY = "container_registry"
    STORAGE_HOST = "storage_host"
    AGENT = "agent"
    KERNEL = "kernel"
    ROUTING = "routing"
    IMAGE = "image"
    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact_registry"
    SESSION_TEMPLATE = "session_template"
    APP_CONFIG = "app_config"
    MODEL_CARD = "model_card"

    # === Root-query-enabled entities (superadmin-only) ===
    RESOURCE_PRESET = "resource_preset"
    USER_RESOURCE_POLICY = "user_resource_policy"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    EVENT_LOG = "event_log"

    # === Admin page access control ===
    PROJECT_ADMIN_PAGE = "project_admin_page"
    DOMAIN_ADMIN_PAGE = "domain_admin_page"

    # === Auto-only entities used in permissions ===
    NOTIFICATION_RULE = "notification_rule"

    # === Auto sub-entities with direct GET APIs ===
    DEPLOYMENT_TOKEN = "deployment:token"
    DEPLOYMENT_POLICY = "deployment:policy"
    DEPLOYMENT_REVISION = "deployment:revision"
    IMAGE_ALIAS = "image:alias"
    ROLE_ASSIGNMENT = "role:assignment"

    # === Sub-entity permissions split from parent metadata access ===
    # These split permission control of a parent entity into sub-aspects so that
    # access to listings/detail (parent) and access to internal data or
    # sub-operations (child) can be granted independently.
    VFOLDER_DATA = "vfolder:data"
    SESSION_APP_SERVICE = "session:app_service"
    USER_EMAIL = "user:email"

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


# ---------------------------------------------------------------------------
# Per-entity allowed-operation tables
#
# These tables define which operations are valid for a given role-kind on a
# given entity. Entity types not listed in an override map fall back to the
# corresponding default set. The helper functions are cached because the
# answer is purely a function of the inputs.
# ---------------------------------------------------------------------------

_STANDARD_OPS: frozenset[OperationType] = frozenset({
    OperationType.CREATE,
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.SOFT_DELETE,
    OperationType.HARD_DELETE,
})
_READ_ONLY_OPS: frozenset[OperationType] = frozenset({OperationType.READ})

_DEFAULT_ADMIN_OPS: frozenset[OperationType] = _STANDARD_OPS
_DEFAULT_OWNER_OPS: frozenset[OperationType] = _STANDARD_OPS
_DEFAULT_MEMBER_OPS: frozenset[OperationType] = _READ_ONLY_OPS

# vfolder:data CRUD on internal files/directories — soft-delete is intentionally
# omitted because there is no two-stage delete for vfolder data.
_VFOLDER_DATA_OWNER_OPS: frozenset[OperationType] = frozenset({
    OperationType.CREATE,
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.HARD_DELETE,
})

_ADMIN_OPS_OVERRIDES: Mapping[RBACElementType, frozenset[OperationType]] = {
    # vfolder:data and session:app_service are owner-only — admins of the parent scope
    # have access to listings/metadata but not to internal data or app endpoints.
    RBACElementType.VFOLDER_DATA: frozenset(),
    RBACElementType.SESSION_APP_SERVICE: frozenset(),
}
_OWNER_OPS_OVERRIDES: Mapping[RBACElementType, frozenset[OperationType]] = {
    RBACElementType.VFOLDER_DATA: _VFOLDER_DATA_OWNER_OPS,
    RBACElementType.SESSION_APP_SERVICE: _READ_ONLY_OPS,
}
_MEMBER_OPS_OVERRIDES: Mapping[RBACElementType, frozenset[OperationType]] = {
    # Members of a project may create their own sessions, vfolders,
    # and model deployments (a.k.a. model services).
    RBACElementType.SESSION: frozenset({OperationType.READ, OperationType.CREATE}),
    RBACElementType.VFOLDER: frozenset({OperationType.READ, OperationType.CREATE}),
    RBACElementType.MODEL_DEPLOYMENT: frozenset({
        OperationType.READ,
        OperationType.CREATE,
    }),
    # Owner-only sub-entities — members of the parent scope have no access.
    RBACElementType.VFOLDER_DATA: frozenset(),
    RBACElementType.SESSION_APP_SERVICE: frozenset(),
}


@functools.cache
def admin_operations(entity_type: RBACElementType) -> frozenset[OperationType]:
    """Operations granted to an *admin* role on the given entity type."""
    return _ADMIN_OPS_OVERRIDES.get(entity_type, _DEFAULT_ADMIN_OPS)


@functools.cache
def owner_operations(entity_type: RBACElementType) -> frozenset[OperationType]:
    """Operations granted to an *owner* role on the given entity type."""
    return _OWNER_OPS_OVERRIDES.get(entity_type, _DEFAULT_OWNER_OPS)


@functools.cache
def member_operations(entity_type: RBACElementType) -> frozenset[OperationType]:
    """Operations granted to a *member* role on the given entity type."""
    return _MEMBER_OPS_OVERRIDES.get(entity_type, _DEFAULT_MEMBER_OPS)


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
