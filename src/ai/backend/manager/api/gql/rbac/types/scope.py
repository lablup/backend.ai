"""GraphQL scope types for RBAC system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from .enums import ScopeTypeGQL

if TYPE_CHECKING:
    from ai.backend.manager.data.permission.id import ScopeId as ScopeIdData
    from ai.backend.manager.data.permission.permission_group import PermissionGroupExtendedData


@strawberry.type(
    description="Added in 26.2.0. Scope represents a level in the permission hierarchy"
)
class Scope(Node):
    id: NodeID[str]
    type: ScopeTypeGQL
    guest: bool = strawberry.field(
        default=False,
        description="Added in 26.2.0. True if this is a guest permission group (scope visibility only)",
    )

    @classmethod
    def from_permission_group(cls, data: PermissionGroupExtendedData) -> Self:
        return cls(
            type=data.scope_id.scope_type,
            id=ID(data.scope_id.scope_id),
            guest=len(data.permissions) == 0,
        )

    @classmethod
    def from_dataclass(cls, data: ScopeIdData, *, guest: bool = False) -> Self:
        """Create Scope from ScopeIdData (without permissions)."""
        return cls(
            type=data.scope_type,
            id=ID(data.scope_id),
            guest=guest,
        )


ScopeEdge = Edge[Scope]


@strawberry.type(description="Added in 26.2.0. Connection type for paginated scopes")
class ScopeConnection(Connection[Scope]):
    count: int

    def __init__(self, *args, count: int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
