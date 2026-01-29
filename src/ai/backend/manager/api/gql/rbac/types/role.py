"""GraphQL role types for RBAC system."""

from __future__ import annotations

from typing import Optional, Self, override

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.permission_controller.options import RoleConditions, RoleOrders

from .enums import EntityTypeGQL, RoleOrderField, RoleSourceGQL, ScopeTypeGQL
from .role_info import RoleIdentityInfo, RoleLifecycleInfo

# ==============================================================================
# Filter Types
# ==============================================================================


@strawberry.input(description="Added in 26.2.0. Filter for scope type")
class ScopeTypeFilter:
    in_: Optional[list[ScopeTypeGQL]] = strawberry.field(default=None, name="in")
    equals: Optional[ScopeTypeGQL] = None


@strawberry.input(description="Added in 26.2.0. Filter for role source")
class RoleSourceFilter:
    in_: Optional[list[RoleSourceGQL]] = strawberry.field(default=None, name="in")
    equals: Optional[RoleSourceGQL] = None


@strawberry.input(description="Added in 26.2.0. Filter options for role queries")
class RoleFilter(GQLFilter):
    scope_type: Optional[ScopeTypeFilter] = None
    scope_id: Optional[ID] = None
    source: Optional[RoleSourceFilter] = None
    name: Optional[StringFilter] = None
    has_permission_for: Optional[EntityTypeGQL] = None

    AND: Optional[list[RoleFilter]] = None
    OR: Optional[list[RoleFilter]] = None
    NOT: Optional[list[RoleFilter]] = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=RoleConditions.by_name_contains,
                equals_factory=RoleConditions.by_name_equals,
                starts_with_factory=RoleConditions.by_name_starts_with,
                ends_with_factory=RoleConditions.by_name_ends_with,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply scope_type filter
        if self.scope_type:
            if self.scope_type.equals:
                field_conditions.append(RoleConditions.by_scope_type(self.scope_type.equals))
            elif self.scope_type.in_:
                type_conditions = [RoleConditions.by_scope_type(st) for st in self.scope_type.in_]
                field_conditions.append(combine_conditions_or(type_conditions))

        # Apply scope_id filter
        if self.scope_id:
            field_conditions.append(RoleConditions.by_scope_id(str(self.scope_id)))

        # Apply source filter
        if self.source:
            if self.source.equals:
                field_conditions.append(RoleConditions.by_sources([self.source.equals]))
            elif self.source.in_:
                field_conditions.append(RoleConditions.by_sources(list(self.source.in_)))

        # Apply has_permission_for filter
        if self.has_permission_for:
            field_conditions.append(RoleConditions.by_has_permission_for(self.has_permission_for))

        # Handle logical operators
        if self.AND:
            and_conditions = [cond for f in self.AND for cond in f.build_conditions()]
            if and_conditions:
                field_conditions.extend(and_conditions)

        if self.OR:
            or_conditions = [cond for f in self.OR for cond in f.build_conditions()]
            if or_conditions:
                field_conditions.append(combine_conditions_or(or_conditions))

        if self.NOT:
            not_conditions = [cond for f in self.NOT for cond in f.build_conditions()]
            if not_conditions:
                field_conditions.append(negate_conditions(not_conditions))

        return field_conditions if field_conditions else []


# ==============================================================================
# OrderBy Types
# ==============================================================================


@strawberry.input(description="Added in 26.2.0. Ordering options for role queries")
class RoleOrderBy(GQLOrderBy):
    field: RoleOrderField
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case RoleOrderField.NAME:
                return RoleOrders.name(ascending)
            case RoleOrderField.CREATED_AT:
                return RoleOrders.created_at(ascending)
            case RoleOrderField.UPDATED_AT:
                return RoleOrders.updated_at(ascending)


# ==============================================================================
# Object Types
# ==============================================================================


@strawberry.type(
    description="Added in 26.2.0. Role: defines a collection of permissions bound to specific scopes"
)
class Role(Node):
    id: NodeID[str]
    identity: RoleIdentityInfo = strawberry.field(
        description="Added in 26.2.0. Identity information for this role",
    )
    lifecycle: RoleLifecycleInfo = strawberry.field(
        description="Added in 26.2.0. Lifecycle information for this role",
    )

    @classmethod
    def from_data(cls, data: RoleData) -> Self:
        return cls(
            id=ID(str(data.id)),
            identity=RoleIdentityInfo(
                name=data.name,
                description=data.description,
                source=data.source,
            ),
            lifecycle=RoleLifecycleInfo(
                status=data.status,
                created_at=data.created_at,
                updated_at=data.updated_at,
                deleted_at=data.deleted_at,
            ),
        )

    @classmethod
    def from_detail_data(cls, data: RoleDetailData) -> Self:
        return cls(
            id=ID(str(data.id)),
            identity=RoleIdentityInfo(
                name=data.name,
                description=data.description,
                source=data.source,
            ),
            lifecycle=RoleLifecycleInfo(
                status=data.status,
                created_at=data.created_at,
                updated_at=data.updated_at,
                deleted_at=data.deleted_at,
            ),
        )


# ==============================================================================
# Connection Types (Relay Specification)
# ==============================================================================


RoleEdge = Edge[Role]


@strawberry.type(description="Added in 26.2.0. Connection type for paginated roles")
class RoleConnection(Connection[Role]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
