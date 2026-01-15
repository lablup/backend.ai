"""GraphQL scope types for RBAC system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Self

import strawberry
from strawberry import ID
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.data.permission.id import ScopeId as ScopeIdData
from ai.backend.manager.data.permission.permission import PermissionData

from .enums import ScopeTypeGQL
from .helper import paginate_in_memory
from .permission import ScopedPermission, ScopedPermissionConnection, ScopedPermissionEdge

if TYPE_CHECKING:
    from ai.backend.manager.data.permission.permission_group import PermissionGroupExtendedData


@strawberry.type(description="Scope represents a level in the permission hierarchy")
class Scope:
    type: ScopeTypeGQL
    id: ID
    guest: bool = strawberry.field(
        default=False,
        description="True if this is a guest permission group (scope visibility only)",
    )

    _permissions: strawberry.Private[list[PermissionData]]

    @strawberry.field(description="Permissions granted within this scope")
    def permissions(
        self,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ScopedPermissionConnection:
        """Fetch scoped permissions with optional pagination."""
        all_perms = [ScopedPermission.from_dataclass(p) for p in self._permissions]

        result = paginate_in_memory(all_perms, first, after, last, before, limit, offset)

        edges = [
            ScopedPermissionEdge(node=perm, cursor=encode_cursor(str(perm.id)))
            for perm in result.items
        ]

        return ScopedPermissionConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=result.total_count,
        )

    @classmethod
    def from_permission_group(cls, data: PermissionGroupExtendedData) -> Self:
        return cls(
            type=data.scope_id.scope_type,
            id=ID(data.scope_id.scope_id),
            guest=len(data.permissions) == 0,
            _permissions=data.permissions,
        )

    @classmethod
    def from_dataclass(cls, data: ScopeIdData, *, guest: bool = False) -> Self:
        """Create Scope from ScopeIdData (without permissions)."""
        return cls(
            type=data.scope_type,
            id=ID(data.scope_id),
            guest=guest,
            _permissions=[],
        )
