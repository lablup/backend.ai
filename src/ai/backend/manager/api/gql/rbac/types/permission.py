"""GraphQL permission types for RBAC system."""

from __future__ import annotations

from typing import Optional, Self

import strawberry
from strawberry import ID
from strawberry.relay import Node, NodeID

from ai.backend.manager.data.permission.id import ScopeId as ScopeIdData
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.permission_group import PermissionGroupExtendedData

from .enums import EntityTypeGQL, OperationTypeGQL, ScopeTypeGQL


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
