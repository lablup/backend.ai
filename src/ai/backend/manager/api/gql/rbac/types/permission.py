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
        # Scope resolution depends on the scope_type and requires loading the
        # appropriate entity. This is deferred as it involves complex entity
        # resolution logic that varies by scope type.
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
