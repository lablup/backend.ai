"""Prometheus query preset GQL Node, Edge, Connection, and mutation payload types."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from .payloads import PrometheusPresetOptionsGQL

if TYPE_CHECKING:
    from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData


@strawberry.type(
    name="PrometheusQueryPreset",
    description="Prometheus query preset entity implementing Relay Node pattern.",
)
class PrometheusQueryPresetGQL(Node):
    id: NodeID[str] = strawberry.field(description="Preset UUID (primary key).")
    name: str = strawberry.field(description="Human-readable preset identifier.")
    metric_name: str = strawberry.field(description="Prometheus metric name.")
    query_template: str = strawberry.field(description="PromQL template with placeholders.")
    time_window: str | None = strawberry.field(
        description="Preset-specific default window. Falls back to server config if null."
    )
    options: PrometheusPresetOptionsGQL = strawberry.field(
        description="Preset options including filter and group labels."
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
            options=PrometheusPresetOptionsGQL(
                filter_labels=data.filter_labels,
                group_labels=data.group_labels,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


PrometheusQueryPresetEdge = Edge[PrometheusQueryPresetGQL]


@strawberry.type(description="Paginated connection for prometheus query preset records.")
class PrometheusQueryPresetConnection(Connection[PrometheusQueryPresetGQL]):
    count: int = strawberry.field(
        description="Total number of preset records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.type(
    name="CreatePrometheusQueryPresetPayload",
    description="Payload returned after creating a preset.",
)
class CreatePrometheusQueryPresetPayload:
    preset: PrometheusQueryPresetGQL


@strawberry.type(
    name="ModifyPrometheusQueryPresetPayload",
    description="Payload returned after modifying a preset.",
)
class ModifyPrometheusQueryPresetPayload:
    preset: PrometheusQueryPresetGQL
