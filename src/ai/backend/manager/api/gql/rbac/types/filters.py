"""GraphQL filter and order types for RBAC queries."""

from __future__ import annotations

import uuid
from typing import override

import strawberry
from strawberry import ID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.permission_controller.options import (
    PermissionGroupConditions,
    PermissionGroupOrders,
    RoleConditions,
    RoleOrders,
)

from .enums import PermissionGroupOrderField, RoleOrderField, RoleSourceGQL, ScopeTypeGQL


@strawberry.input(description="Filter for role source")
class RoleSourceFilter:
    in_: list[RoleSourceGQL] | None = strawberry.field(default=None, name="in")
    equals: RoleSourceGQL | None = None


@strawberry.input(description="Filter options for role queries")
class RoleFilter(GQLFilter):
    source: RoleSourceFilter | None = None
    name: StringFilter | None = None

    AND: list[RoleFilter] | None = None
    OR: list[RoleFilter] | None = None
    NOT: list[RoleFilter] | None = None

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

        # Apply source filter
        if self.source:
            if self.source.equals:
                internal_sources = [self.source.equals.to_internal()]
                field_conditions.append(RoleConditions.by_sources(internal_sources))
            elif self.source.in_:
                internal_sources = [s.to_internal() for s in self.source.in_]
                field_conditions.append(RoleConditions.by_sources(internal_sources))

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


@strawberry.input(description="Ordering options for role queries")
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


@strawberry.input(description="Filter for scope type in permission groups")
class ScopeTypeFilter:
    in_: list[ScopeTypeGQL] | None = strawberry.field(default=None, name="in")
    equals: ScopeTypeGQL | None = None


@strawberry.input(description="Filter options for permission group queries")
class PermissionGroupFilter(GQLFilter):
    role_id: ID | None = None
    scope_type: ScopeTypeFilter | None = None

    AND: list[PermissionGroupFilter] | None = None
    OR: list[PermissionGroupFilter] | None = None
    NOT: list[PermissionGroupFilter] | None = None

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        field_conditions: list[QueryCondition] = []

        # Apply role_id filter
        if self.role_id:
            field_conditions.append(PermissionGroupConditions.by_role_id(uuid.UUID(self.role_id)))

        # Apply scope_type filter
        if self.scope_type:
            if self.scope_type.equals:
                field_conditions.append(
                    PermissionGroupConditions.by_scope_type(self.scope_type.equals.to_internal())
                )
            elif self.scope_type.in_:
                # Multiple scope types - combine with OR
                scope_conditions = [
                    PermissionGroupConditions.by_scope_type(s.to_internal())
                    for s in self.scope_type.in_
                ]
                field_conditions.append(combine_conditions_or(scope_conditions))

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


@strawberry.input(description="Ordering options for permission group queries")
class PermissionGroupOrderBy(GQLOrderBy):
    field: PermissionGroupOrderField
    direction: OrderDirection = OrderDirection.ASC

    @override
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case PermissionGroupOrderField.SCOPE_TYPE:
                return PermissionGroupOrders.scope_type(ascending)
            case PermissionGroupOrderField.SCOPE_ID:
                return PermissionGroupOrders.scope_id(ascending)
