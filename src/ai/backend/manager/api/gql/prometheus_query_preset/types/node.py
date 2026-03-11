"""Prometheus query preset GQL Node, Edge, Connection, and mutation payload types."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from .payloads import QueryDefinitionOptionsGQL

if TYPE_CHECKING:
    from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData


@strawberry.type(
    name="QueryDefinition",
    description="Added in 26.3.0. Prometheus query definition entity implementing Relay Node pattern.",
)
class QueryDefinitionGQL(Node):
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
        return cls(
            id=ID(str(data.id)),
            name=data.name,
            metric_name=data.metric_name,
            query_template=data.query_template,
            time_window=data.time_window,
            options=QueryDefinitionOptionsGQL(
                filter_labels=data.filter_labels,
                group_labels=data.group_labels,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


QueryDefinitionEdge = Edge[QueryDefinitionGQL]


@strawberry.type(
    description="Added in 26.3.0. Paginated connection for query definition records.",
)
class QueryDefinitionConnection(Connection[QueryDefinitionGQL]):
    count: int = strawberry.field(
        description="Total number of query definition records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(
    name="CreateQueryDefinitionPayload",
    description="Added in 26.3.0. Payload returned after creating a query definition.",
)
class CreateQueryDefinitionPayload:
    preset: QueryDefinitionGQL


@strawberry.type(
    name="ModifyQueryDefinitionPayload",
    description="Added in 26.3.0. Payload returned after modifying a query definition.",
)
class ModifyQueryDefinitionPayload:
    preset: QueryDefinitionGQL
