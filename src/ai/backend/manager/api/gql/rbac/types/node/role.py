"""GraphQL Role node, edge, and connection types."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Self

import strawberry
from strawberry import ID, Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.manager.api.gql.rbac.fetcher import (
    fetch_object_permissions,
    fetch_permission_groups,
    fetch_scoped_permissions,
)
from ai.backend.manager.api.gql.rbac.types.enums import RoleSourceGQL
from ai.backend.manager.api.gql.rbac.types.filters import (
    ObjectPermissionFilter,
    PermissionGroupFilter,
    ScopedPermissionFilter,
)
from ai.backend.manager.api.gql.rbac.types.node.permission import (
    ObjectPermissionConnection,
    PermissionGroupConnection,
    ScopedPermissionConnection,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData


@strawberry.type(description="Role: defines a collection of permissions bound to a specific scope")
class Role(Node):
    id: NodeID[str]
    name: str
    description: str | None
    source: RoleSourceGQL
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None

    # Private field for deferred loading
    _role_id: strawberry.Private[uuid.UUID]

    @strawberry.field(description="Permission groups for this role")  # type: ignore[misc]
    async def permission_groups(
        self,
        info: Info[StrawberryGQLContext],
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PermissionGroupConnection:
        """Fetch permission groups with pagination (deferred resolution)."""
        return await fetch_permission_groups(
            info,
            filter=PermissionGroupFilter(role_id=ID(str(self._role_id))),
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )

    @strawberry.field(description="Scoped permissions for this role")  # type: ignore[misc]
    async def scoped_permissions(
        self,
        info: Info[StrawberryGQLContext],
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ScopedPermissionConnection:
        """Fetch scoped permissions with pagination (deferred resolution)."""
        return await fetch_scoped_permissions(
            info,
            filter=ScopedPermissionFilter(role_id=ID(str(self._role_id))),
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )

    @strawberry.field(description="Object permissions for this role")  # type: ignore[misc]
    async def object_permissions(
        self,
        info: Info[StrawberryGQLContext],
        first: int | None = None,
        after: str | None = None,
        last: int | None = None,
        before: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> ObjectPermissionConnection:
        """Fetch object permissions with pagination (deferred resolution)."""
        return await fetch_object_permissions(
            info,
            filter=ObjectPermissionFilter(role_id=ID(str(self._role_id))),
            before=before,
            after=after,
            first=first,
            last=last,
            limit=limit,
            offset=offset,
        )

    @classmethod
    def from_data(cls, data: RoleData) -> Self:
        """Create Role from RoleData."""
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            source=RoleSourceGQL.from_internal(data.source),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            _role_id=data.id,
        )

    @classmethod
    def from_detail_data(cls, data: RoleDetailData) -> Self:
        """Create Role from RoleDetailData (backward compatible)."""
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            description=data.description,
            source=RoleSourceGQL.from_internal(data.source),
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            _role_id=data.id,
        )


RoleEdge = Edge[Role]


@strawberry.type(description="Connection for paginated role results")
class RoleConnection(Connection[Role]):
    count: int = strawberry.field(description="Total number of roles matching the query criteria.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
