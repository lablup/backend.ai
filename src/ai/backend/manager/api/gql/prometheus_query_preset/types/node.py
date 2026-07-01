"""Prometheus query preset GQL Node, Edge, Connection, and mutation payload types."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    CreateQueryDefinitionGQLPayload as CreateQueryDefinitionGQLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    ModifyQueryDefinitionGQLPayload as ModifyQueryDefinitionGQLPayloadDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    QueryDefinitionNode,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .category import CategoryGQL
from .payloads import QueryDefinitionOptionsGQL


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Prometheus query definition entity implementing Relay Node pattern.",
    ),
    name="QueryDefinition",
)
class QueryDefinitionGQL(PydanticNodeMixin[QueryDefinitionNode]):
    id: NodeID[str] = gql_field(description="Query definition UUID (primary key).")
    name: str = gql_field(description="Human-readable query definition identifier.")
    description: str | None = gql_field(description="Human-readable description.")
    rank: int = gql_field(description="Sort rank (lower = higher priority).")
    category_id: UUID | None = gql_field(description="Category UUID.")
    metric_name: str = gql_field(description="Prometheus metric name.")
    query_template: str = gql_field(description="PromQL template with placeholders.")
    time_window: str | None = gql_field(
        description="Default time window. Falls back to server config if null."
    )
    options: QueryDefinitionOptionsGQL = gql_field(
        description="Query definition options including filter and group labels."
    )
    created_at: datetime = gql_field(description="Creation timestamp.")
    updated_at: datetime = gql_field(description="Last update timestamp.")

    @gql_added_field(
        BackendAIGQLMeta(added_version="26.4.3", description="Resolved category entity.")
    )  # type: ignore[misc]
    async def category(self, info: Info[StrawberryGQLContext]) -> CategoryGQL | None:
        if self.category_id is None:
            return None
        return await info.context.data_loaders.category_loader.load(self.category_id)


QueryDefinitionEdge = Edge[QueryDefinitionGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Paginated connection for query definition records.",
    ),
)
class QueryDefinitionConnection(Connection[QueryDefinitionGQL]):
    count: int = gql_field(
        description="Total number of query definition records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after creating a query definition.",
    ),
    model=CreateQueryDefinitionGQLPayloadDTO,
    name="CreateQueryDefinitionPayload",
)
class CreateQueryDefinitionPayload(PydanticOutputMixin[CreateQueryDefinitionGQLPayloadDTO]):
    """Payload for query definition creation mutation."""

    preset: QueryDefinitionGQL = gql_field(description="Created query definition.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after modifying a query definition.",
    ),
    model=ModifyQueryDefinitionGQLPayloadDTO,
    name="ModifyQueryDefinitionPayload",
)
class ModifyQueryDefinitionPayload(PydanticOutputMixin[ModifyQueryDefinitionGQLPayloadDTO]):
    """Payload for query definition modification mutation."""

    preset: QueryDefinitionGQL = gql_field(description="Updated query definition.")
