"""Role preset GQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.role_preset.response import RolePresetNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
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
    RolePermissionPresetFilterGQL,
    RolePermissionPresetOrderByGQL,
)


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
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
            added_version=NEXT_RELEASE_VERSION,
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
        raise NotImplementedError


RolePresetEdge = Edge[RolePresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
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
