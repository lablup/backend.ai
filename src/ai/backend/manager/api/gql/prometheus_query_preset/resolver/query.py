"""Prometheus query preset GQL query resolvers."""

from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info
from strawberry.relay import PageInfo

from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    SearchQueryDefinitionsInput,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    ExecuteQueryDefinitionOptionsInput,
    QueryDefinitionConnection,
    QueryDefinitionEdge,
    QueryDefinitionFilter,
    QueryDefinitionGQL,
    QueryDefinitionOrderBy,
    QueryDefinitionResultGQL,
    QueryTimeRangeInput,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types.payloads import MetricResultGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.prometheus_query_preset import ExecutePresetOptions
from ai.backend.manager.services.prometheus_query_preset.actions import (
    ExecutePresetAction,
    GetPresetAction,
)


@strawberry.field(description="Added in 26.3.0. Get a single query definition by ID (admin only).")  # type: ignore[misc]
async def admin_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> QueryDefinitionGQL | None:
    check_admin_only()
    processors = info.context.processors
    action_result = await processors.prometheus_query_preset.get_preset.wait_for_complete(
        GetPresetAction(preset_id=UUID(id))
    )
    return QueryDefinitionGQL.from_data(action_result.preset)


@strawberry.field(
    description="Added in 26.3.0. List query definitions with filtering and pagination (admin only)."
)  # type: ignore[misc]
async def admin_prometheus_query_presets(
    info: Info[StrawberryGQLContext],
    filter: QueryDefinitionFilter | None = None,
    order_by: list[QueryDefinitionOrderBy] | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> QueryDefinitionConnection | None:
    check_admin_only()

    pydantic_filter = filter.to_pydantic() if filter else None
    pydantic_order = [o.to_pydantic() for o in order_by] if order_by else None

    payload = await info.context.adapters.prometheus_query_preset.admin_search(
        SearchQueryDefinitionsInput(
            filter=pydantic_filter,
            order=pydantic_order,
            limit=limit if limit is not None else 50,
            offset=offset if offset is not None else 0,
        )
    )

    nodes = [QueryDefinitionGQL.from_pydantic(node) for node in payload.items]
    edges = [QueryDefinitionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return QueryDefinitionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@strawberry.field(
    description="Added in 26.3.0. Execute a query definition by ID and return the result (admin only)."
)  # type: ignore[misc]
async def admin_prometheus_query_preset_result(
    info: Info[StrawberryGQLContext],
    id: ID,
    time_range: QueryTimeRangeInput | None = None,
    options: ExecuteQueryDefinitionOptionsInput | None = None,
    time_window: str | None = None,
) -> QueryDefinitionResultGQL:
    check_admin_only()
    processors = info.context.processors

    execute_options = (
        options.to_internal()
        if options is not None
        else ExecutePresetOptions(filter_labels={}, group_labels=[])
    )

    action_result = await processors.prometheus_query_preset.execute_preset.wait_for_complete(
        ExecutePresetAction(
            preset_id=UUID(id),
            options=execute_options,
            time_window=time_window,
            time_range=time_range.to_internal() if time_range is not None else None,
        )
    )

    response = action_result.response

    return QueryDefinitionResultGQL(
        status=response.status,
        result_type=response.data.result_type,
        result=[
            MetricResultGQL.from_metric_response(metric_response)
            for metric_response in response.data.result
        ],
    )
