"""AppConfigPolicy GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.app_config_policy.response import AppConfigPolicyNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Scoped app-config policy.",
    ),
    name="AppConfigPolicy",
)
class AppConfigPolicyGQL(PydanticNodeMixin[AppConfigPolicyNode]):
    id: NodeID[str] = gql_field(description="Policy row UUID.")
    config_name: str = gql_field(description="Unique, immutable policy name.")
    scope_sources: list[str] = gql_field(
        description="Ordered scope chain (low → high merge priority).",
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime | None = gql_field(description="Last update timestamp.")


AppConfigPolicyEdgeGQL = Edge[AppConfigPolicyGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Connection type for paginated app-config policy results.",
    ),
    name="AppConfigPolicyConnection",
)
class AppConfigPolicyConnectionGQL(Connection[AppConfigPolicyGQL]):
    count: int = gql_field(description="Total number of policies matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
