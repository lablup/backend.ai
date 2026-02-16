"""GraphQL types for RBAC entity search."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Self, override

import strawberry
from strawberry import ID, Info
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.rbac.types.entity_node import EntityNode
from ai.backend.manager.api.gql.rbac.types.permission import EntityTypeGQL
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesData,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.repositories.permission_controller.options import (
    EntityScopeConditions,
    EntityScopeOrders,
)

# ==================== Enums ====================


@strawberry.enum(description="Added in 26.3.0. Entity ordering field")
class EntityOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    REGISTERED_AT = "registered_at"


# ==================== Node Types ====================


@strawberry.type(
    name="EntityRef",
    description="Added in 26.3.0. Entity reference from the association_scopes_entities table",
)
class EntityRefGQL(Node):
    id: NodeID[str]
    scope_type: EntityTypeGQL
    scope_id: str
    entity_type: EntityTypeGQL
    entity_id: str
    registered_at: datetime

    @strawberry.field(  # type: ignore[misc]
        description="The resolved entity object."
    )
    async def entity(
        self,
        *,
        info: Info[StrawberryGQLContext],
    ) -> EntityNode | None:
        raise NotImplementedError

    @classmethod
    async def resolve_nodes(  # type: ignore[override]
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        raise NotImplementedError

    @classmethod
    def from_dataclass(cls, data: AssociationScopesEntitiesData) -> Self:
        return cls(
            id=ID(str(data.id)),
            scope_type=EntityTypeGQL.from_internal(data.scope_id.scope_type.to_entity_type()),
            scope_id=data.scope_id.scope_id,
            entity_type=EntityTypeGQL.from_internal(data.object_id.entity_type),
            entity_id=data.object_id.entity_id,
            registered_at=data.registered_at,
        )


# ==================== Filter Types ====================


@strawberry.input(description="Added in 26.3.0. Filter for entity associations")
class EntityFilter(GQLFilter):
    entity_type: EntityTypeGQL | None = None
    entity_id: StringFilter | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if self.entity_type is not None:
            conditions.append(EntityScopeConditions.by_entity_type(self.entity_type.to_internal()))

        if self.entity_id is not None:
            condition = self.entity_id.build_query_condition(
                contains_factory=EntityScopeConditions.by_entity_id_contains,
                equals_factory=EntityScopeConditions.by_entity_id_equals,
                starts_with_factory=EntityScopeConditions.by_entity_id_starts_with,
                ends_with_factory=EntityScopeConditions.by_entity_id_ends_with,
            )
            if condition:
                conditions.append(condition)

        return conditions


# ==================== OrderBy Types ====================


@strawberry.input(description="Added in 26.3.0. Order by specification for entity associations")
class EntityOrderBy(GQLOrderBy):
    field: EntityOrderField
    direction: OrderDirection = OrderDirection.DESC

    @override
    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case EntityOrderField.ENTITY_TYPE:
                return EntityScopeOrders.entity_type(ascending)
            case EntityOrderField.REGISTERED_AT:
                return EntityScopeOrders.registered_at(ascending)


# ==================== Connection Types ====================


@strawberry.type(description="Added in 26.3.0. Entity edge")
class EntityEdge:
    node: EntityRefGQL
    cursor: str


@strawberry.type(description="Added in 26.3.0. Entity connection")
class EntityConnection:
    edges: list[EntityEdge]
    page_info: strawberry.relay.PageInfo
    count: int
