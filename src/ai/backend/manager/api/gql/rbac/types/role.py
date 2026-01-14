"""GraphQL role types for RBAC system."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Self, TypeVar, override

import strawberry
from strawberry import ID
from strawberry.relay import Node, NodeID, PageInfo

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter, encode_cursor
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.permission.id import ScopeId as ScopeIdData
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission_group import PermissionGroupExtendedData
from ai.backend.manager.data.permission.role import RoleDetailData
from ai.backend.manager.data.permission.types import ScopeType as ScopeTypeInternal
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.permission_controller.options import RoleConditions, RoleOrders

from .enums import EntityTypeGQL, RoleOrderField, RoleSourceGQL, ScopeTypeGQL
from .permission import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
    Scope,
    ScopedPermission,
    ScopedPermissionConnection,
    ScopedPermissionEdge,
)

# ==============================================================================
# Filter Types
# ==============================================================================


@strawberry.input(description="Filter for scope type")
class ScopeTypeFilter:
    in_: Optional[list[ScopeTypeGQL]] = strawberry.field(default=None, name="in")
    equals: Optional[ScopeTypeGQL] = None


@strawberry.input(description="Filter for role source")
class RoleSourceFilter:
    in_: Optional[list[RoleSourceGQL]] = strawberry.field(default=None, name="in")
    equals: Optional[RoleSourceGQL] = None


@strawberry.input(description="Filter options for role queries")
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
                internal_type = self.scope_type.equals.to_internal()
                field_conditions.append(RoleConditions.by_scope_type(internal_type))
            elif self.scope_type.in_:
                type_conditions = [
                    RoleConditions.by_scope_type(st.to_internal()) for st in self.scope_type.in_
                ]
                field_conditions.append(combine_conditions_or(type_conditions))

        # Apply scope_id filter
        if self.scope_id:
            field_conditions.append(RoleConditions.by_scope_id(str(self.scope_id)))

        # Apply source filter
        if self.source:
            if self.source.equals:
                internal_sources = [self.source.equals.to_internal()]
                field_conditions.append(RoleConditions.by_sources(internal_sources))
            elif self.source.in_:
                internal_sources = [s.to_internal() for s in self.source.in_]
                field_conditions.append(RoleConditions.by_sources(internal_sources))

        # Apply has_permission_for filter
        if self.has_permission_for:
            internal_entity_type = self.has_permission_for.to_internal()
            field_conditions.append(RoleConditions.by_has_permission_for(internal_entity_type))

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


# ==============================================================================
# Helper Functions
# ==============================================================================

T = TypeVar("T")


def _paginate_list(
    items: list[T],
    first: Optional[int],
    after: Optional[str],
    last: Optional[int],
    before: Optional[str],
    limit: Optional[int],
    offset: Optional[int],
) -> tuple[list[T], bool, bool, int]:
    """Simple in-memory pagination for lists.

    Returns:
        tuple of (paginated_items, has_next_page, has_previous_page, total_count)
    """
    total = len(items)

    # Offset-based pagination takes precedence if provided
    if limit is not None or offset is not None:
        start = offset or 0
        end = start + (limit or 25)
        paginated = items[start:end]
        has_next = end < total
        has_prev = start > 0
    else:
        # Cursor-based (simplified)
        paginated = items[:first] if first else items
        has_next = bool(first and len(items) > first)
        has_prev = False

    return paginated, has_next, has_prev, total


# ==============================================================================
# Object Types
# ==============================================================================


@strawberry.type(description="Role: defines a collection of permissions bound to a specific scope")
class Role(Node):
    id: NodeID[str]
    name: str
    description: Optional[str]
    scope: Scope
    source: RoleSourceGQL
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    additional_scopes: list[Scope]

    # Private fields for lazy loading
    # TODO: Refactor to fetch permissions via separate DB queries instead of in-memory pagination.
    #       Currently, all permissions are loaded upfront and paginated in memory.
    #       For better performance, implement DB-level pagination by:
    #       1. Adding separate service actions (e.g., GetRoleScopedPermissionsAction)
    #       2. Using fetcher functions that query permissions independently
    #       3. Passing `info.context` to resolver methods for DB access
    _permission_groups: strawberry.Private[list[PermissionGroupExtendedData]]
    _object_permissions_data: strawberry.Private[list[ObjectPermissionData]]

    @strawberry.field(description="Scoped permissions for this role")
    def scoped_permissions(
        self,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ScopedPermissionConnection:
        """Fetch scoped permissions with optional pagination."""
        # Flatten permissions from permission groups
        all_perms = [
            ScopedPermission.from_permission_group(pg, perm)
            for pg in self._permission_groups
            for perm in pg.permissions
        ]

        # Apply in-memory pagination
        paginated, has_next, has_prev, total = _paginate_list(
            all_perms, first, after, last, before, limit, offset
        )

        edges = [
            ScopedPermissionEdge(node=perm, cursor=encode_cursor(str(perm.id)))
            for perm in paginated
        ]

        return ScopedPermissionConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=has_prev,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=total,
        )

    @strawberry.field(description="Object permissions for this role")
    def object_permissions(
        self,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ObjectPermissionConnection:
        """Fetch object permissions with optional pagination."""
        all_perms = [ObjectPermission.from_dataclass(op) for op in self._object_permissions_data]

        # Apply in-memory pagination
        paginated, has_next, has_prev, total = _paginate_list(
            all_perms, first, after, last, before, limit, offset
        )

        edges = [
            ObjectPermissionEdge(node=perm, cursor=encode_cursor(str(perm.id)))
            for perm in paginated
        ]

        return ObjectPermissionConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=has_prev,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=total,
        )

    @classmethod
    def from_dataclass(cls, data: RoleDetailData) -> Self:
        # Extract scope from permission groups (use first one, or create default)
        scope_id_data = (
            data.permission_groups[0].scope_id
            if data.permission_groups
            else ScopeIdData(scope_type=ScopeTypeInternal.GLOBAL, scope_id="")
        )

        # TODO: Implement additional scopes extraction from object permissions
        additional_scopes: list[Scope] = []

        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            scope=Scope.from_dataclass(scope_id_data),
            source=RoleSourceGQL.from_internal(data.source),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            additional_scopes=additional_scopes,
            # Store raw data for lazy loading
            _permission_groups=data.permission_groups,
            _object_permissions_data=data.object_permissions,
        )


# ==============================================================================
# Connection Types (Relay Specification)
# ==============================================================================


@strawberry.type(description="Edge type for role connections")
class RoleEdge:
    node: Role
    cursor: str


@strawberry.type(description="Connection for paginated role results")
class RoleConnection:
    page_info: strawberry.relay.PageInfo
    edges: list[RoleEdge]
    count: int

    def __init__(
        self, *, edges: list[RoleEdge], page_info: strawberry.relay.PageInfo, count: int
    ) -> None:
        self.edges = edges
        self.page_info = page_info
        self.count = count
