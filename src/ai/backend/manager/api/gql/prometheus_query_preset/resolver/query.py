"""Prometheus query preset GQL query resolvers."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.prometheus_query_preset.fetcher import (
    fetch_prometheus_query_preset,
    fetch_prometheus_query_preset_result,
    fetch_prometheus_query_presets,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    MetricLabelEntryInput,
    QueryDefinitionConnection,
    QueryDefinitionFilter,
    QueryDefinitionGQL,
    QueryDefinitionOrderBy,
    QueryDefinitionResultGQL,
    QueryTimeRangeInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.field(description="Added in 26.3.0. Get a single query definition by ID (admin only).")  # type: ignore[misc]
async def admin_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> QueryDefinitionGQL | None:
    check_admin_only()
    return await fetch_prometheus_query_preset(info, preset_id=uuid.UUID(id))


@strawberry.field(
    description="Added in 26.3.0. List query definitions with filtering and pagination (admin only)."
)  # type: ignore[misc]
async def admin_prometheus_query_presets(
    info: Info[StrawberryGQLContext],
    filter: QueryDefinitionFilter | None = None,
    order_by: list[QueryDefinitionOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> QueryDefinitionConnection | None:
    check_admin_only()
    return await fetch_prometheus_query_presets(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )


@strawberry.field(
    description="Added in 26.3.0. Execute a query definition by ID and return the result (admin only)."
)  # type: ignore[misc]
async def admin_prometheus_query_preset_result(
    info: Info[StrawberryGQLContext],
    id: ID,
    time_range: QueryTimeRangeInput | None = None,
    labels: list[MetricLabelEntryInput] | None = None,
    group_labels: list[str] | None = None,
    time_window: str | None = None,
) -> QueryDefinitionResultGQL:
    check_admin_only()
    options = MetricLabelEntryInput.to_execute_options(labels, group_labels)

    return await fetch_prometheus_query_preset_result(
        info,
        preset_id=uuid.UUID(id),
        options=options,
        time_window=time_window,
        time_range=time_range.to_query_time_range() if time_range is not None else None,
    )
