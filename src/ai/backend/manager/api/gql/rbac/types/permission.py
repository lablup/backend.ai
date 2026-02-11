"""GraphQL types for RBAC permission management."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Self, override

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.api.gql.base import OrderDirection
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.permission_controller.creators import PermissionCreatorSpec
from ai.backend.manager.repositories.permission_controller.options import (
    ScopedPermissionConditions,
    ScopedPermissionOrders,
)

# ==================== Enums ====================


@strawberry.enum(name="EntityType", description="RBAC entity type")
class EntityTypeGQL(StrEnum):
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
    def from_internal(cls, value: EntityType) -> EntityTypeGQL:
        return cls(value.value)

    def to_internal(self) -> EntityType:
        return EntityType(self.value)


@strawberry.enum(name="OperationType", description="RBAC operation type")
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
        return cls(value.value)

    def to_internal(self) -> OperationType:
        return OperationType(self.value)


@strawberry.enum(name="ScopeType", description="RBAC scope type")
class ScopeTypeGQL(StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    GLOBAL = "global"

    @classmethod
    def from_internal(cls, value: ScopeType) -> ScopeTypeGQL:
        return cls(value.value)

    def to_internal(self) -> ScopeType:
        return ScopeType(self.value)


@strawberry.enum
class PermissionOrderField(StrEnum):
    ID = "id"
    ENTITY_TYPE = "entity_type"


# ==================== Node Types ====================


@strawberry.type(description="RBAC scoped permission")
class PermissionGQL(Node):
    id: NodeID[str]
    _role_id: strawberry.Private[uuid.UUID]
    scope_type: ScopeTypeGQL
    scope_id: str
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL

    @strawberry.field(description="The role ID this permission belongs to.")  # type: ignore[misc]
    def role_id(self) -> ID:
        return ID(str(self._role_id))

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        # TODO: Implement after adding batch get permission method to repository
        return []

    @classmethod
    def from_dataclass(cls, data: PermissionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            _role_id=data.role_id,
            scope_type=ScopeTypeGQL.from_internal(data.scope_type),
            scope_id=data.scope_id,
            entity_type=EntityTypeGQL.from_internal(data.entity_type),
            operation=OperationTypeGQL.from_internal(data.operation),
        )


# ==================== Filter Types ====================


@strawberry.input(description="Filter for scoped permissions")
class PermissionFilter(GQLFilter):
    role_id: uuid.UUID | None = None
    scope_type: ScopeTypeGQL | None = None
    entity_type: EntityTypeGQL | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.role_id is not None:
            conditions.append(ScopedPermissionConditions.by_role_id(self.role_id))

        if self.scope_type is not None:
            conditions.append(
                ScopedPermissionConditions.by_scope_type(self.scope_type.to_internal())
            )

        if self.entity_type is not None:
            conditions.append(
                ScopedPermissionConditions.by_entity_type(self.entity_type.to_internal())
            )

        return conditions


# ==================== OrderBy Types ====================


@strawberry.input(description="Order by specification for permissions")
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


@strawberry.input(description="Input for creating a scoped permission")
class CreatePermissionInput:
    role_id: uuid.UUID
    scope_type: ScopeTypeGQL
    scope_id: str
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL

    def to_creator(self) -> Creator[PermissionRow]:
        return Creator(
            spec=PermissionCreatorSpec(
                role_id=self.role_id,
                scope_type=self.scope_type.to_internal(),
                scope_id=self.scope_id,
                entity_type=self.entity_type.to_internal(),
                operation=self.operation.to_internal(),
            )
        )


# ==================== Connection Types ====================


PermissionEdge = Edge[PermissionGQL]


@strawberry.type(description="Permission connection")
class PermissionConnection(Connection[PermissionGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
