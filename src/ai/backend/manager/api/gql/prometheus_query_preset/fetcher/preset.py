"""Prometheus query preset GQL data fetcher functions."""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    MetricLabelEntryGQL,
    MetricResultGQL,
    MetricResultValueGQL,
    QueryDefinitionConnection,
    QueryDefinitionEdge,
    QueryDefinitionFilter,
    QueryDefinitionGQL,
    QueryDefinitionOrderBy,
    QueryDefinitionResultGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.data.prometheus_query_preset import ExecutePresetOptions
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.prometheus_query_preset.options import (
    PrometheusQueryPresetConditions,
    PrometheusQueryPresetOrders,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    ExecutePresetAction,
    GetPresetAction,
    SearchPresetsAction,
)


@lru_cache(maxsize=1)
def get_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=PrometheusQueryPresetOrders.created_at(ascending=False),
        backward_order=PrometheusQueryPresetOrders.created_at(ascending=True),
        forward_condition_factory=PrometheusQueryPresetConditions.by_cursor_forward,
        backward_condition_factory=PrometheusQueryPresetConditions.by_cursor_backward,
        tiebreaker_order=PrometheusQueryPresetRow.id.asc(),
    )


async def fetch_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    preset_id: UUID,
) -> QueryDefinitionGQL:
    processors = info.context.processors
    action_result = await processors.prometheus_query_preset.get_preset.wait_for_complete(
        GetPresetAction(preset_id=preset_id)
    )
    return QueryDefinitionGQL.from_data(action_result.preset)


async def fetch_prometheus_query_presets(
    info: Info[StrawberryGQLContext],
    filter: QueryDefinitionFilter | None = None,
    order_by: list[QueryDefinitionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> QueryDefinitionConnection:
    processors = info.context.processors

    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_preset_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=None,
    )

    action_result = await processors.prometheus_query_preset.search_presets.wait_for_complete(
        SearchPresetsAction(querier=querier)
    )

    nodes = [QueryDefinitionGQL.from_data(data) for data in action_result.items]
    edges = [QueryDefinitionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return QueryDefinitionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_prometheus_query_preset_result(
    info: Info[StrawberryGQLContext],
    preset_id: UUID,
    options: ExecutePresetOptions,
    time_window: str | None,
    time_range: QueryTimeRange | None,
) -> QueryDefinitionResultGQL:
    processors = info.context.processors

    action_result = await processors.prometheus_query_preset.execute_preset.wait_for_complete(
        ExecutePresetAction(
            preset_id=preset_id,
            options=options,
            time_window=time_window,
            time_range=time_range,
        )
    )

    response = action_result.response
    result_entries: list[MetricResultGQL] = []
    for metric_response in response.data.result:
        metric_labels = [
            MetricLabelEntryGQL(key=k, value=str(v))
            for k, v in metric_response.metric.model_dump(exclude_none=True).items()
        ]
        values = [
            MetricResultValueGQL(timestamp=ts, value=val) for ts, val in metric_response.values
        ]
        result_entries.append(MetricResultGQL(metric=metric_labels, values=values))

    return QueryDefinitionResultGQL(
        status=response.status,
        result_type=response.data.result_type,
        result=result_entries,
    )
