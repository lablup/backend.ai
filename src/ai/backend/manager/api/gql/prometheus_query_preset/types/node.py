"""Prometheus query preset GQL Node, Edge, Connection, and mutation payload types."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID
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
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

from .payloads import QueryDefinitionOptionsGQL

if TYPE_CHECKING:
    from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Prometheus query definition entity implementing Relay Node pattern.",
    ),
    name="QueryDefinition",
)
class QueryDefinitionGQL(PydanticNodeMixin[QueryDefinitionNode]):
    id: NodeID[str] = strawberry.field(description="Query definition UUID (primary key).")
    name: str = strawberry.field(description="Human-readable query definition identifier.")
    metric_name: str = strawberry.field(description="Prometheus metric name.")
    query_template: str = strawberry.field(description="PromQL template with placeholders.")
    time_window: str | None = strawberry.field(
        description="Default time window. Falls back to server config if null."
    )
    options: QueryDefinitionOptionsGQL = strawberry.field(
        description="Query definition options including filter and group labels."
    )
    created_at: datetime = strawberry.field(description="Creation timestamp.")
    updated_at: datetime = strawberry.field(description="Last update timestamp.")

    @classmethod
    def from_data(cls, data: PrometheusQueryPresetData) -> Self:
        from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
            QueryDefinitionOptionsInfo,
        )

        return cls(
            id=ID(str(data.id)),
            name=data.name,
            metric_name=data.metric_name,
            query_template=data.query_template,
            time_window=data.time_window,
            options=QueryDefinitionOptionsGQL.from_pydantic(
                QueryDefinitionOptionsInfo(
                    filter_labels=data.filter_labels,
                    group_labels=data.group_labels,
                )
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    @classmethod
    def from_pydantic(
        cls,
        dto: QueryDefinitionNode,
        extra: dict[str, Any] | None = None,
        *,
        id_field: str = "id",
    ) -> Self:
        from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
            QueryDefinitionOptionsInfo,
        )

        return cls(
            id=ID(str(dto.id)),
            name=dto.name,
            metric_name=dto.metric_name,
            query_template=dto.query_template,
            time_window=dto.time_window,
            options=QueryDefinitionOptionsGQL.from_pydantic(
                QueryDefinitionOptionsInfo(
                    filter_labels=dto.options.filter_labels,
                    group_labels=dto.options.group_labels,
                )
            ),
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


QueryDefinitionEdge = Edge[QueryDefinitionGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Paginated connection for query definition records.",
    ),
)
class QueryDefinitionConnection(Connection[QueryDefinitionGQL]):
    count: int = strawberry.field(
        description="Total number of query definition records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after creating a query definition.",
    ),
    name="CreateQueryDefinitionPayload",
)
class CreateQueryDefinitionPayload:
    """Payload for query definition creation mutation."""

    preset: QueryDefinitionGQL = strawberry.field(description="Created query definition.")

    @classmethod
    def from_pydantic(cls, dto: CreateQueryDefinitionGQLPayloadDTO) -> Self:
        return cls(preset=QueryDefinitionGQL.from_pydantic(dto.preset))


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Payload returned after modifying a query definition.",
    ),
    name="ModifyQueryDefinitionPayload",
)
class ModifyQueryDefinitionPayload:
    """Payload for query definition modification mutation."""

    preset: QueryDefinitionGQL = strawberry.field(description="Updated query definition.")

    @classmethod
    def from_pydantic(cls, dto: ModifyQueryDefinitionGQLPayloadDTO) -> Self:
        return cls(preset=QueryDefinitionGQL.from_pydantic(dto.preset))
