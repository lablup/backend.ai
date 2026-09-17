"""GraphQL types for RBAC scope input and shared enums."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityTypeScope,
    PermissionBitDTO,
    ScopeInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)

# Re-export for stable import paths in audit_log scope
__all__ = (
    "EntityTypeScopeGQL",
    "RBACElementTypeFilterGQL",
    "RBACElementTypeGQL",
    "ScopeInputGQL",
)

# ==================== Input Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope reference for associating an entity with a scope.",
        added_version="26.4.2",
    ),
    name="ScopeInput",
)
class ScopeInputGQL(PydanticInputMixin[ScopeInputDTO]):
    scope_type: str
    scope_id: str


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Entity reference parametrized by RBAC element type.",
        added_version="26.4.4",
    ),
    name="EntityTypeScope",
)
class EntityTypeScopeGQL(PydanticInputMixin[EntityTypeScope]):
    entity_type: str = gql_field(
        description="Type of the entity.",
    )
    entity_id: str = gql_field(
        description="ID of the entity.",
    )


PermissionBitGQL: type[PermissionBitDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One bit of a permission mask.",
    ),
    PermissionBitDTO,
    name="PermissionBit",
)


# ==================== Deprecated ====================


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Unified RBAC element type for scope-entity relationships.",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="an entity type string",
    ),
    name="RBACElementType",
)
class RBACElementTypeGQL(StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    SESSION = "session"
    VFOLDER = "vfolder"
    MODEL_DEPLOYMENT = "model_deployment"
    KEYPAIR = "keypair"
    NOTIFICATION_CHANNEL = "notification_channel"
    NETWORK = "network"
    IDLE_CHECKER_ASSIGNMENT = "idle_checker_assignment"
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
    APP_CONFIG_DEFINITION = "app_config_definition"
    APP_CONFIG_ALLOW_LIST = "app_config_allow_list"
    APP_CONFIG_FRAGMENT = "app_config_fragment"
    MODEL_CARD = "model_card"
    RESOURCE_PRESET = "resource_preset"
    USER_RESOURCE_POLICY = "user_resource_policy"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    KERNEL_HISTORY = "kernel:history"
    EVENT_LOG = "event_log"
    PROJECT_ADMIN_PAGE = "project_admin_page"
    DOMAIN_ADMIN_PAGE = "domain_admin_page"
    NOTIFICATION_RULE = "notification_rule"
    DEPLOYMENT_TOKEN = "deployment:token"
    DEPLOYMENT_POLICY = "deployment:policy"
    DEPLOYMENT_REVISION = "deployment:revision"
    IMAGE_ALIAS = "image:alias"
    ROLE_ASSIGNMENT = "role:assignment"
    VFOLDER_DATA = "vfolder:data"
    SESSION_APP_SERVICE = "session:app_service"
    USER_EMAIL = "user:email"
    ARTIFACT_REVISION = "artifact_revision"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter for RBAC element type fields (scope_type / entity_type). "
            "Supports equals / in / not_equals / not_in."
        ),
        added_version="26.4.4",
        deprecated_version=NEXT_RELEASE_VERSION,
        deprecation_hint="`StringFilter`",
    ),
    name="RBACElementTypeFilter",
)
class RBACElementTypeFilterGQL(PydanticInputMixin[Any]):
    equals: RBACElementTypeGQL | None = gql_field(
        description="Matches rows with this exact element type.", default=None
    )
    in_: list[RBACElementTypeGQL] | None = gql_field(
        description="Matches rows whose element type is in this list.",
        name="in",
        default=None,
    )
    not_equals: RBACElementTypeGQL | None = gql_field(
        description="Excludes rows with this exact element type.", default=None
    )
    not_in: list[RBACElementTypeGQL] | None = gql_field(
        description="Excludes rows whose element type is in this list.", default=None
    )
