"""GraphQL enum types for RBAC system."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)

EntityTypeGQL: type[EntityType] = strawberry.enum(
    EntityType,
    name="EntityType",
    description="Entity types managed by the RBAC system",
)

OperationTypeGQL: type[OperationType] = strawberry.enum(
    OperationType,
    name="OperationType",
    description="Operations that can be performed on entities",
)

ScopeTypeGQL: type[ScopeType] = strawberry.enum(
    ScopeType,
    name="ScopeType",
    description="Scope types in the permission hierarchy",
)

RoleSourceGQL: type[RoleSource] = strawberry.enum(
    RoleSource,
    name="RoleSource",
    description="Role source indicating how the role was created",
)


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
