"""GraphQL permission types for RBAC system."""

from __future__ import annotations

from typing import Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission import PermissionData

from .enums import EntityTypeGQL, OperationTypeGQL

# ==============================================================================
# Permission Types
# ==============================================================================


@strawberry.type(
    description="Scoped Permission: grants permission for an operation on ALL entities"
)
class ScopedPermission(Node):
    id: NodeID[str]
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL

    @classmethod
    def from_dataclass(cls, data: PermissionData) -> Self:
        return cls(
            id=ID(str(data.id)),
            entity_type=data.entity_type,
            operation=data.operation,
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
            entity_type=data.object_id.entity_type,
            entity_id=ID(data.object_id.entity_id),
            operation=data.operation,
        )


# ==============================================================================
# Connection Types
# ==============================================================================


ScopedPermissionEdge = Edge[ScopedPermission]


class ScopedPermissionConnection(Connection[ScopedPermission]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


ObjectPermissionEdge = Edge[ObjectPermission]


class ObjectPermissionConnection(Connection[ObjectPermission]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
