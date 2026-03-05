"""Prometheus query preset GQL query resolvers."""

from __future__ import annotations

import uuid

import strawberry
from strawberry import ID, Info

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.exception import PrometheusQueryPresetNotFound
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
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.prometheus_query_preset.options import (
    PrometheusQueryPresetConditions,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    SearchPresetsAction,
)


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
    description=(
        "Execute a prometheus query preset by name and return the query result. "
        "Available to all authenticated users."
    )
)  # type: ignore[misc]
async def prometheus_query_preset_result(
    info: Info[StrawberryGQLContext],
    name: str,
    time_range: QueryTimeRangeInput,
    labels: list[MetricLabelEntryInput] | None = None,
    group_labels: list[str] | None = None,
    window: str | None = None,
) -> PrometheusQueryResultGQL:
    processors = info.context.processors

    # Resolve name → preset_id via search
    name_spec = StringMatchSpec(value=name, negated=False, case_insensitive=False)
    querier = BatchQuerier(
        conditions=[PrometheusQueryPresetConditions.by_name_equals(name_spec)],
        orders=[],
        pagination=OffsetPagination(limit=1, offset=0),
    )
    search_result = await processors.prometheus_query_preset.search_presets.wait_for_complete(
        SearchPresetsAction(querier=querier)
    )
    if not search_result.items:
        raise PrometheusQueryPresetNotFound(f"Prometheus query preset '{name}' not found")

    preset_data = search_result.items[0]
    options = MetricLabelEntryInput.to_execute_options(labels, group_labels)

    return await fetch_prometheus_query_preset_result(
        info,
        preset_id=preset_data.id,
        options=options,
        window=window,
        time_range=time_range.to_query_time_range(),
    )
