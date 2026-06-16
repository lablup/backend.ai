"""AppConfigFragment GQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config_fragment.response import AppConfigFragmentNode
from ai.backend.common.dto.manager.v2.app_config_fragment.types import AppConfigScopeType
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

# The shared DTO enum is auto-registered by Strawberry the first time it
# is referenced as a typed field. Re-export under the ``GQL`` suffix so
# other modules can write `from ... import AppConfigScopeTypeGQL`. Calling
# `strawberry.enum(...)` here would clash with that auto-registration
# under the same `"AppConfigScopeType"` name.
AppConfigScopeTypeGQL = AppConfigScopeType


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Raw per-scope app-config fragment.",
    ),
    name="AppConfigFragment",
)
class AppConfigFragmentGQL(PydanticNodeMixin[AppConfigFragmentNode]):
    id: NodeID[str] = gql_field(description="Fragment row UUID.")
    scope_type: AppConfigScopeType = gql_field(description="Scope type.")
    scope_id: str = gql_field(description="Scope id.")
    name: str = gql_field(description="Config name.")
    rank: int = gql_field(description="Merge priority within `name` (low → high).")
    config: JSON | None = gql_field(description="Raw configuration payload, or null.")
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")


AppConfigFragmentEdgeGQL = Edge[AppConfigFragmentGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Connection type for paginated app-config fragment results.",
    ),
    name="AppConfigFragmentConnection",
)
class AppConfigFragmentConnectionGQL(Connection[AppConfigFragmentGQL]):
    count: int = gql_field(description="Total number of fragments matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
