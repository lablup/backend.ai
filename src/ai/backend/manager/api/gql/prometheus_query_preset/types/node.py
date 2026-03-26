"""Prometheus query preset GQL Node, Edge, Connection, and mutation payload types."""

from __future__ import annotations

from datetime import datetime
from typing import Any

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
    gql_connection_type,
    gql_field,
    gql_node_type,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin

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
