"""GraphQL permission node, edge, and connection types."""

from __future__ import annotations

from typing import Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.rbac.types.enums import (
    EntityTypeGQL,
    OperationTypeGQL,
    ScopeTypeGQL,
)
from ai.backend.manager.data.permission.id import ScopeId as ScopeIdData
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.permission_group import PermissionGroupData


@strawberry.type(description="Scope represents a level in the permission hierarchy")
class Scope:
    type: ScopeTypeGQL
    id: ID | None

    @classmethod
    def from_dataclass(cls, data: ScopeIdData) -> Self:
        return cls(
            type=ScopeTypeGQL.from_internal(data.scope_type),
            id=ID(data.scope_id) if data.scope_id else None,
        )


@strawberry.type(description="Permission Group: groups permissions by scope")
class PermissionGroup(Node):
    """Permission group that groups permissions by scope."""

    id: NodeID[str]
    scope: Scope

    @classmethod
    def from_data(cls, data: PermissionGroupData) -> Self:
        """Create PermissionGroup from PermissionGroupData."""
        return cls(
            id=ID(str(data.id)),
            scope=Scope.from_dataclass(data.scope_id),
        )


@strawberry.type(
    description="Scoped Permission: grants permission for an operation on ALL entities"
)
class ScopedPermission(Node):
    id: NodeID[str]
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL

    @classmethod
    def from_data(cls, data: PermissionData) -> Self:
        """Create ScopedPermission from PermissionData."""
        return cls(
            id=ID(str(data.id)),
            entity_type=EntityTypeGQL.from_internal(data.entity_type),
            operation=OperationTypeGQL.from_internal(data.operation),
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


# ==============================================================================
# Connection Types
# ==============================================================================


ScopedPermissionEdge = Edge[ScopedPermission]


@strawberry.type(description="Connection for paginated scoped permission results")
class ScopedPermissionConnection(Connection[ScopedPermission]):
    count: int = strawberry.field(
        description="Total number of scoped permissions matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


ObjectPermissionEdge = Edge[ObjectPermission]


@strawberry.type(description="Connection for paginated object permission results")
class ObjectPermissionConnection(Connection[ObjectPermission]):
    count: int = strawberry.field(
        description="Total number of object permissions matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


PermissionGroupEdge = Edge[PermissionGroup]


@strawberry.type(description="Connection for paginated permission group results")
class PermissionGroupConnection(Connection[PermissionGroup]):
    count: int = strawberry.field(
        description="Total number of permission groups matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
