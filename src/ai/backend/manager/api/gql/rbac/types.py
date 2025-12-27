"""GraphQL types, filters, and inputs for RBAC system."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional, Self, override

import strawberry
from strawberry import ID
from strawberry.relay import Node, NodeID

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy
from ai.backend.manager.data.permission.id import ScopeId as ScopeIdData
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.permission_group import PermissionGroupExtendedData
from ai.backend.manager.data.permission.role import RoleDetailData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType as EntityTypeInternal,
)
from ai.backend.manager.data.permission.types import (
    OperationType as OperationTypeInternal,
)
from ai.backend.manager.data.permission.types import (
    RoleSource as RoleSourceInternal,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as ScopeTypeInternal,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import (
    Creator,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import RoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.options import RoleConditions, RoleOrders
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

# ==============================================================================
# GraphQL Enum Types
# ==============================================================================


@strawberry.enum(name="EntityType", description="Entity types managed by the RBAC system")
class EntityTypeGQL(StrEnum):
    COMPUTE_SESSION = "compute_session"
    VFOLDER = "vfolder"
    IMAGE = "image"
    MODEL_SERVICE = "model_service"
    MODEL_ARTIFACT = "model_artifact"
    AGENT = "agent"
    RESOURCE_GROUP = "resource_group"
    STORAGE_HOST = "storage_host"
    APP_CONFIG = "app_config"
    NOTIFICATION = "notification"
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    ROLE = "role"
    ROLE_ASSIGNMENT = "role_assignment"

    @classmethod
    def from_internal(cls, internal_type: EntityTypeInternal) -> EntityTypeGQL:
        """Convert internal EntityType to GraphQL enum."""
        # Map internal "session" to GQL "compute_session"
        if internal_type == EntityTypeInternal.SESSION:
            return cls.COMPUTE_SESSION
        return cls(internal_type.value)

    def to_internal(self) -> EntityTypeInternal:
        """Convert GraphQL enum to internal EntityType."""
        # Map GQL "compute_session" to internal "session"
        if self == EntityTypeGQL.COMPUTE_SESSION:
            return EntityTypeInternal.SESSION
        return EntityTypeInternal(self.value)


@strawberry.enum(name="OperationType", description="Operations that can be performed on entities")
class OperationTypeGQL(StrEnum):
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
    def from_internal(cls, internal_type: OperationTypeInternal) -> OperationTypeGQL:
        """Convert internal OperationType to GraphQL enum."""
        return cls(internal_type.value)

    def to_internal(self) -> OperationTypeInternal:
        """Convert GraphQL enum to internal OperationType."""
        return OperationTypeInternal(self.value)


@strawberry.enum(name="ScopeType", description="Scope types in the permission hierarchy")
class ScopeTypeGQL(StrEnum):
    GLOBAL = "global"
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"

    @classmethod
    def from_internal(cls, internal_type: ScopeTypeInternal) -> ScopeTypeGQL:
        """Convert internal ScopeType to GraphQL enum."""
        return cls(internal_type.value)

    def to_internal(self) -> ScopeTypeInternal:
        """Convert GraphQL enum to internal ScopeType."""
        return ScopeTypeInternal(self.value)


@strawberry.enum(name="RoleSource", description="Role source indicating how the role was created")
class RoleSourceGQL(StrEnum):
    SYSTEM = "system"
    CUSTOM = "custom"

    @classmethod
    def from_internal(cls, internal_type: RoleSourceInternal) -> RoleSourceGQL:
        """Convert internal RoleSource to GraphQL enum."""
        return cls(internal_type.value)

    def to_internal(self) -> RoleSourceInternal:
        """Convert GraphQL enum to internal RoleSource."""
        return RoleSourceInternal(self.value)


@strawberry.enum(name="RoleOrderField", description="Fields available for ordering role queries")
class RoleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.enum(
    name="ScopedPermissionOrderField",
    description="Fields available for ordering scoped permission queries",
)
class ScopedPermissionOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    SCOPE_TYPE = "scope_type"


@strawberry.enum(
    name="ObjectPermissionOrderField",
    description="Fields available for ordering object permission queries",
)
class ObjectPermissionOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    ENTITY_ID = "entity_id"
    OPERATION = "operation"


# ==============================================================================
# GraphQL Object Types
# ==============================================================================


@strawberry.type(description="Scope represents a level in the permission hierarchy")
class Scope:
    type: ScopeTypeGQL
    id: Optional[ID]

    @classmethod
    def from_dataclass(cls, data: ScopeIdData) -> Self:
        return cls(
            type=ScopeTypeGQL.from_internal(data.scope_type),
            id=ID(data.scope_id) if data.scope_id else None,
        )


@strawberry.type(
    description="Scoped Permission: grants permission for an operation on ALL entities"
)
class ScopedPermission(Node):
    id: NodeID[str]
    scope_type: ScopeTypeGQL
    scope_id: ID
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL

    @classmethod
    def from_permission_group(cls, pg: PermissionGroupExtendedData, perm: PermissionData) -> Self:
        return cls(
            id=ID(str(perm.id)),
            scope_type=ScopeTypeGQL.from_internal(pg.scope_id.scope_type),
            scope_id=ID(pg.scope_id.scope_id),
            entity_type=EntityTypeGQL.from_internal(perm.entity_type),
            operation=OperationTypeGQL.from_internal(perm.operation),
        )


@strawberry.type(description="Object Permission: grants permission for a SPECIFIC entity instance")
class ObjectPermission(Node):
    id: NodeID[str]
    entity_type: EntityTypeGQL
    entity_id: ID
    operation: OperationTypeGQL

    @classmethod
    def from_dataclass(cls, data: ObjectPermissionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            entity_type=EntityTypeGQL.from_internal(data.object_id.entity_type),
            entity_id=ID(data.object_id.entity_id),
            operation=OperationTypeGQL.from_internal(data.operation),
        )


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

    # Non-paginated nested fields
    scoped_permissions: list[ScopedPermission]
    object_permissions: list[ObjectPermission]
    additional_scopes: list[Scope]

    @classmethod
    def from_dataclass(cls, data: RoleDetailData) -> Self:
        # Extract scope from permission groups (use first one, or create default)
        scope_id_data = (
            data.permission_groups[0].scope_id
            if data.permission_groups
            else ScopeIdData(scope_type=ScopeTypeInternal.GLOBAL, scope_id="")
        )

        # Flatten scoped permissions from all permission groups
        scoped_perms = [
            ScopedPermission.from_permission_group(pg, perm)
            for pg in data.permission_groups
            for perm in pg.permissions
        ]

        # Convert object permissions
        obj_perms = [ObjectPermission.from_dataclass(op) for op in data.object_permissions]

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
            scoped_permissions=scoped_perms,
            object_permissions=obj_perms,
            additional_scopes=additional_scopes,
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

    AND: Optional[list[RoleFilter]] = None  # noqa: N815
    OR: Optional[list[RoleFilter]] = None  # noqa: N815
    NOT: Optional[list[RoleFilter]] = None  # noqa: N815

    @override
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        field_conditions: list[QueryCondition] = []

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=RoleConditions.by_name_contains,
                equals_factory=RoleConditions.by_name_equals,
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
# Input Types
# ==============================================================================


@strawberry.input(description="Input for specifying a scope in mutations")
class ScopeInput:
    type: ScopeTypeGQL
    id: Optional[ID] = None


@strawberry.input(description="Input for creating a new custom role")
class CreateRoleInput:
    name: str
    description: Optional[str] = None
    scope: ScopeInput

    def to_creator(self) -> Creator[RoleRow]:
        """Convert to Creator for repository."""
        return Creator(
            spec=RoleCreatorSpec(
                name=self.name,
                source=RoleSourceInternal.CUSTOM,
                status=RoleStatus.ACTIVE,
                description=self.description,
            )
        )


@strawberry.input(description="Input for updating an existing role")
class UpdateRoleInput:
    id: ID
    name: Optional[str] = None
    description: Optional[str] = None

    def to_updater(self) -> Updater[RoleRow]:
        """Convert to Updater for repository."""
        return Updater(
            spec=RoleUpdaterSpec(
                name=OptionalState.update(self.name) if self.name else OptionalState.nop(),
                description=TriState.update(self.description)
                if self.description
                else TriState.nop(),
            ),
            pk_value=uuid.UUID(self.id),
        )


@strawberry.input(description="Input for scoped permissions")
class ScopedPermissionInput:
    scope_type: ScopeTypeGQL
    scope_id: ID
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL


@strawberry.input(description="Input for object permissions")
class ObjectPermissionInput:
    entity_type: EntityTypeGQL
    entity_id: ID
    operation: OperationTypeGQL


@strawberry.input(description="Input for updating role permissions")
class UpdateRolePermissionsInput:
    role_id: ID
    scoped_permissions_to_add: Optional[list[ScopedPermissionInput]] = None
    object_permissions_to_add: Optional[list[ObjectPermissionInput]] = None
    scoped_permission_ids_to_delete: Optional[list[ID]] = None
    object_permission_ids_to_delete: Optional[list[ID]] = None


@strawberry.input(description="Input for creating a role assignment")
class CreateRoleAssignmentInput:
    user_id: ID
    role_id: ID
    scope: ScopeInput
    expires_at: Optional[datetime] = None


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

    def __init__(self, *, edges: list[RoleEdge], page_info: strawberry.relay.PageInfo, count: int):
        self.edges = edges
        self.page_info = page_info
        self.count = count
