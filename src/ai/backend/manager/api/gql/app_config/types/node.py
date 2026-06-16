"""AppConfig (merged view) GQL Node, Edge, and Connection types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID

import strawberry
from strawberry.relay import Connection, Edge, NodeID
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.app_config.response import AppConfigNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

if TYPE_CHECKING:
    from ai.backend.manager.api.gql.app_config_fragment.types.node import AppConfigFragmentGQL


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Merged per-user AppConfig view. `id` is the composite "
            "`{userId}:{name}` (the merged view is a derived value, not a "
            "table row); `fragments` are ordered low → high merge priority; "
            "`config` is the deep-merge result and is null when every "
            "contributing fragment is empty."
        ),
    ),
    name="AppConfig",
)
class AppConfigGQL(PydanticNodeMixin[AppConfigNode]):
    id: NodeID[str] = gql_field(description="Composite id `{userId}:{name}`.")
    user_id: UUID = gql_field(description="Target user's UUID.")
    name: str = gql_field(description="Policy / config name.")
    # Use `strawberry.lazy()` to break the import cycle between
    # `app_config.types.node` and `app_config_fragment.types.node`:
    # the fragment package's `__init__.py` eagerly loads its resolver,
    # which imports `MyBulkCreate*` payloads back from `app_config.types`.
    fragments: list[
        Annotated[
            AppConfigFragmentGQL,
            strawberry.lazy("ai.backend.manager.api.gql.app_config_fragment.types.node"),
        ]
    ] = gql_field(
        description="Contributing fragments in merge order (low → high).",
    )
    config: JSON | None = gql_field(
        description="Deep-merged configuration, or null when every fragment is empty.",
    )


AppConfigEdgeGQL = Edge[AppConfigGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Connection type for paginated merged AppConfig results.",
    ),
    name="AppConfigConnection",
)
class AppConfigConnectionGQL(Connection[AppConfigGQL]):
    count: int = gql_field(description="Total number of AppConfigs matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
