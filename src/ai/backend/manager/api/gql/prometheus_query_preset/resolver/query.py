"""Prometheus query preset GQL query resolvers."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import ID, Info

from ai.backend.manager.api.gql.prometheus_query_preset.fetcher import (
    fetch_admin_prometheus_query_preset,
    fetch_admin_prometheus_query_presets,
    fetch_prometheus_query_preset_result,
)
from ai.backend.manager.api.gql.prometheus_query_preset.types import (
    MetricLabelEntryInput,
    PrometheusQueryPresetConnection,
    PrometheusQueryPresetFilter,
    PrometheusQueryPresetGQL,
    PrometheusQueryPresetOrderBy,
    PrometheusQueryResultGQL,
    QueryTimeRangeInput,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.field(description="Get a single prometheus query preset by ID (admin only).")  # type: ignore[misc]
async def admin_prometheus_query_preset(
    info: Info[StrawberryGQLContext],
    id: ID,
) -> PrometheusQueryPresetGQL | None:
    check_admin_only()
    return await fetch_admin_prometheus_query_preset(info, preset_id=uuid.UUID(id))


@strawberry.field(
    description="List prometheus query presets with filtering and pagination (admin only)."
)  # type: ignore[misc]
async def admin_prometheus_query_presets(
    info: Info[StrawberryGQLContext],
    filter: PrometheusQueryPresetFilter | None = None,
    order_by: list[PrometheusQueryPresetOrderBy] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> PrometheusQueryPresetConnection | None:
    check_admin_only()
    return await fetch_admin_prometheus_query_presets(
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
    description="Execute a prometheus query preset by ID and return the query result (admin only)."
)  # type: ignore[misc]
async def admin_prometheus_query_preset_result(
    info: Info[StrawberryGQLContext],
    id: ID,
    time_range: QueryTimeRangeInput | None = None,
    labels: list[MetricLabelEntryInput] | None = None,
    group_labels: list[str] | None = None,
    window: str | None = None,
) -> PrometheusQueryResultGQL:
    check_admin_only()
    options = MetricLabelEntryInput.to_execute_options(labels, group_labels)

    return await fetch_prometheus_query_preset_result(
        info,
        preset_id=uuid.UUID(id),
        options=options,
        window=window,
        time_range=time_range.to_query_time_range() if time_range is not None else None,
    )
