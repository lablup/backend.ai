"""GraphQL types for RBAC permission management."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, Self, override

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.permission.types import (
    OperationType,
    RBACElementType,
)
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.permission_controller.creators import PermissionCreatorSpec
from ai.backend.manager.repositories.permission_controller.options import (
    ScopedPermissionConditions,
    ScopedPermissionOrders,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.rbac.types.role import RoleGQL

# ==================== Enums ====================


@strawberry.enum(
    name="RBACElementType",
    description="Added in 26.3.0. Unified RBAC element type for scope-entity relationships",
)
class RBACElementTypeGQL(StrEnum):
    # Scope hierarchy
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"

    # Root-query-enabled entities (scoped)
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

    # Root-query-enabled entities (superadmin-only)
    RESOURCE_PRESET = "resource_preset"
    USER_RESOURCE_POLICY = "user_resource_policy"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    EVENT_LOG = "event_log"

    # Auto-only entities used in permissions
    NOTIFICATION_RULE = "notification_rule"

    # Entity-level scopes
    ARTIFACT_REVISION = "artifact_revision"

    @classmethod
    def from_element(cls, value: RBACElementType) -> RBACElementTypeGQL:
        return cls(value.value)

    def to_element(self) -> RBACElementType:
        return RBACElementType(self.value)


@strawberry.enum(name="OperationType", description="Added in 26.3.0. RBAC operation type")
class OperationTypeGQL(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    SOFT_DELETE = "soft-delete"
    HARD_DELETE = "hard-delete"
    GRANT_ALL = "grant:all"
    GRANT_READ = "grant:read"
    GRANT_UPDATE = "grant:update"
    GRANT_SOFT_DELETE = "grant:soft-delete"
    GRANT_HARD_DELETE = "grant:hard-delete"

    @classmethod
    def from_internal(cls, value: OperationType) -> OperationTypeGQL:
        try:
            return cls(value.value)
        except ValueError:
            raise InvalidAPIParameters(
                extra_msg=f"{value.value!r} is not a valid OperationTypeGQL"
            ) from None

    def to_internal(self) -> OperationType:
        try:
            return OperationType(self.value)
        except ValueError:
            raise InvalidAPIParameters(
                extra_msg=f"{self.value!r} is not a valid OperationType"
            ) from None


@strawberry.enum(description="Added in 26.3.0. Permission ordering field")
class PermissionOrderField(StrEnum):
    ID = "id"
    ENTITY_TYPE = "entity_type"


# ==================== Node Types ====================


@strawberry.type(name="Permission", description="Added in 26.3.0. RBAC scoped permission")
class PermissionGQL(Node):
    id: NodeID[str]
    role_id: uuid.UUID
    scope_type: RBACElementTypeGQL
    scope_id: str
    entity_type: RBACElementTypeGQL
    operation: OperationTypeGQL

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.permission_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_dataclass(data) if data is not None else None for data in results]

    @strawberry.field(description="The role this permission belongs to.")  # type: ignore[misc]
    async def role(
        self, info: Info[StrawberryGQLContext]
    ) -> (
        Annotated[
            RoleGQL,
            strawberry.lazy("ai.backend.manager.api.gql.rbac.types.role"),
        ]
        | None
    ):
        from ai.backend.manager.api.gql.rbac.types.role import RoleGQL

        data = await info.context.data_loaders.role_loader.load(self.role_id)
        if data is None:
            return None
        return RoleGQL.from_dataclass(data)

    @strawberry.field(  # type: ignore[misc]
        description="The scope this permission applies to."
    )
    async def scope(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNode | None:
        from ai.backend.manager.api.gql.artifact.types import ArtifactRevision
        from ai.backend.manager.api.gql.deployment.types.deployment import ModelDeployment
        from ai.backend.manager.api.gql.domain_v2.types.node import DomainV2GQL
        from ai.backend.manager.api.gql.project_v2.types.node import ProjectV2GQL
        from ai.backend.manager.api.gql.rbac.types.role import RoleGQL
        from ai.backend.manager.api.gql.resource_group.types import ResourceGroupGQL
        from ai.backend.manager.api.gql.user.types.node import UserV2GQL

        element_type = self.scope_type.to_element()
        data_loaders = info.context.data_loaders
        match element_type:
            case RBACElementType.USER:
                user_data = await data_loaders.user_loader.load(uuid.UUID(self.scope_id))
                if user_data is None:
                    return None
                return UserV2GQL.from_data(user_data)
            case RBACElementType.PROJECT:
                project_data = await data_loaders.project_loader.load(uuid.UUID(self.scope_id))
                if project_data is None:
                    return None
                return ProjectV2GQL.from_data(project_data)
            case RBACElementType.DOMAIN:
                domain_data = await data_loaders.domain_loader.load(self.scope_id)
                if domain_data is None:
                    return None
                return DomainV2GQL.from_data(domain_data)
            case RBACElementType.ROLE:
                role_data = await data_loaders.role_loader.load(uuid.UUID(self.scope_id))
                if role_data is None:
                    return None
                return RoleGQL.from_dataclass(role_data)
            case RBACElementType.RESOURCE_GROUP:
                rg_data = await data_loaders.resource_group_loader.load(self.scope_id)
                if rg_data is None:
                    return None
                return ResourceGroupGQL.from_dataclass(rg_data)
            case RBACElementType.MODEL_DEPLOYMENT:
                deploy_data = await data_loaders.deployment_loader.load(uuid.UUID(self.scope_id))
                if deploy_data is None:
                    return None
                return ModelDeployment.from_dataclass(deploy_data)
            case RBACElementType.ARTIFACT_REVISION:
                rev_data = await data_loaders.artifact_revision_loader.load(
                    uuid.UUID(self.scope_id)
                )
                if rev_data is None:
                    return None
                return ArtifactRevision.from_dataclass(rev_data)
            case (
                RBACElementType.SESSION
                | RBACElementType.VFOLDER
                | RBACElementType.DEPLOYMENT
                | RBACElementType.KEYPAIR
                | RBACElementType.NOTIFICATION_CHANNEL
                | RBACElementType.NETWORK
                | RBACElementType.CONTAINER_REGISTRY
                | RBACElementType.STORAGE_HOST
                | RBACElementType.IMAGE
                | RBACElementType.ARTIFACT
                | RBACElementType.ARTIFACT_REGISTRY
                | RBACElementType.SESSION_TEMPLATE
                | RBACElementType.APP_CONFIG
                | RBACElementType.RESOURCE_PRESET
                | RBACElementType.USER_RESOURCE_POLICY
                | RBACElementType.KEYPAIR_RESOURCE_POLICY
                | RBACElementType.PROJECT_RESOURCE_POLICY
                | RBACElementType.AUDIT_LOG
                | RBACElementType.EVENT_LOG
                | RBACElementType.NOTIFICATION_RULE
            ):
                return None

    @classmethod
    def from_dataclass(cls, data: PermissionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            role_id=data.role_id,
            scope_type=RBACElementTypeGQL.from_element(data.scope_type.to_element()),
            scope_id=data.scope_id,
            entity_type=RBACElementTypeGQL.from_element(data.entity_type.to_element()),
            operation=OperationTypeGQL.from_internal(data.operation),
        )


# ==================== Filter Types ====================


@strawberry.input(description="Added in 26.3.0. Filter for scoped permissions")
class PermissionFilter(GQLFilter):
    role_id: uuid.UUID | None = None
    scope_type: RBACElementTypeGQL | None = None
    entity_type: RBACElementTypeGQL | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.role_id is not None:
            conditions.append(ScopedPermissionConditions.by_role_id(self.role_id))

        if self.scope_type is not None:
            conditions.append(
                ScopedPermissionConditions.by_scope_type(
                    self.scope_type.to_element().to_scope_type()
                )
            )

        if self.entity_type is not None:
            conditions.append(
                ScopedPermissionConditions.by_entity_type(
                    self.entity_type.to_element().to_entity_type()
                )
            )

        return conditions


# ==================== OrderBy Types ====================


@strawberry.input(description="Added in 26.3.0. Order by specification for permissions")
class PermissionOrderBy(GQLOrderBy):
    field: PermissionOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case PermissionOrderField.ID:
                return ScopedPermissionOrders.id(ascending)
            case PermissionOrderField.ENTITY_TYPE:
                return ScopedPermissionOrders.entity_type(ascending)


# ==================== Input Types ====================


@strawberry.input(description="Added in 26.3.0. Input for creating a scoped permission")
class CreatePermissionInput:
    role_id: uuid.UUID
    scope_type: RBACElementTypeGQL
    scope_id: str
    entity_type: RBACElementTypeGQL
    operation: OperationTypeGQL

    def to_creator(self) -> Creator[PermissionRow]:
        return Creator(
            spec=PermissionCreatorSpec(
                role_id=self.role_id,
                scope_type=self.scope_type.to_element().to_scope_type(),
                scope_id=self.scope_id,
                entity_type=self.entity_type.to_element().to_entity_type(),
                operation=self.operation.to_internal(),
            )
        )


@strawberry.input(description="Added in 26.3.0. Input for deleting a scoped permission")
class DeletePermissionInput:
    id: uuid.UUID


# ==================== Payload Types ====================


@strawberry.type(description="Added in 26.3.0. Payload for delete permission mutation")
class DeletePermissionPayload:
    id: ID


# ==================== Connection Types ====================


PermissionEdge = Edge[PermissionGQL]


@strawberry.type(description="Added in 26.3.0. Permission connection")
class PermissionConnection(Connection[PermissionGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
