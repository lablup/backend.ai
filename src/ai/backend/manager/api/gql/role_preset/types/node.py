"""Role preset GQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID, PageInfo

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    RolePermissionPresetFilter,
    RolePermissionPresetOrder,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.rbac.types import RBACElementTypeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .permission import (
    RolePermissionPresetConnection,
    RolePermissionPresetEdge,
    RolePermissionPresetFilterGQL,
    RolePermissionPresetGQL,
    RolePermissionPresetOrderByGQL,
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Role preset entity implementing the Relay Node pattern.",
    ),
    name="RolePreset",
)
class RolePresetGQL(PydanticNodeMixin[RolePresetNode]):
    id: NodeID[str] = gql_field(description="Role preset UUID (primary key).")
    name: str = gql_field(description="Role preset name.")
    scope_type: RBACElementTypeGQL = gql_field(
        description="Scope type this preset targets (e.g., domain, project)."
    )
    auto_assign: bool = gql_field(
        description=(
            "Default value for the `auto_assign` flag copied onto roles instantiated "
            "from this preset."
        )
    )
    deleted: bool = gql_field(
        description=(
            "Soft-delete flag. Set by the delete mutation and cleared by the restore "
            "mutation; archived rows are excluded from default searches."
        )
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last modification timestamp.")

    @gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Permission entries carried by this role preset.",
        )
    )  # type: ignore[misc]
    async def permission_presets(
        self,
        info: Info[StrawberryGQLContext],
        filter: RolePermissionPresetFilterGQL | None = None,
        order_by: list[RolePermissionPresetOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> RolePermissionPresetConnection | None:
        filter_dto: RolePermissionPresetFilter | None = filter.to_pydantic() if filter else None
        orders_dto: list[RolePermissionPresetOrder] | None = (
            [o.to_pydantic() for o in order_by] if order_by else None
        )
        search_input = SearchRolePermissionPresetsInput(
            filter=filter_dto,
            order=orders_dto,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
        result = await info.context.adapters.role_preset.search_permission_presets(
            RolePresetID(UUID(str(self.id))), search_input
        )
        edges = [
            RolePermissionPresetEdge(
                node=RolePermissionPresetGQL.from_pydantic(item),
                cursor=str(item.id),
            )
            for item in result.items
        ]
        return RolePermissionPresetConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
            count=result.total_count,
        )


RolePresetEdge = Edge[RolePresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.4.4",
        description="Paginated connection for role preset records.",
    ),
)
class RolePresetConnection(Connection[RolePresetGQL]):
    count: int = gql_field(
        description="Total number of role preset records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
