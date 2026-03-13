"""Adapter for converting Prometheus Query Definition domain data to DTOs."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.clients.prometheus.response import MetricResponse
from ai.backend.common.dto.manager.prometheus_query_preset import (
    MetricLabelEntryDTO,
    MetricValueDTO,
    ModifyQueryDefinitionRequest,
    OrderDirection,
    QueryDefinitionDTO,
    QueryDefinitionFilter,
    QueryDefinitionMetricResult,
    QueryDefinitionOptionsDTO,
    QueryDefinitionOrder,
    QueryDefinitionOrderField,
    SearchQueryDefinitionsRequest,
)
from ai.backend.manager.api.rest.adapter import BaseFilterAdapter
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    Updater,
)
from ai.backend.manager.repositories.prometheus_query_preset.options import (
    PrometheusQueryPresetConditions,
    PrometheusQueryPresetOrders,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState


class PrometheusQueryPresetAdapter(BaseFilterAdapter):
    """Adapter for converting between query definition domain data and DTOs."""

    def convert_to_dto(self, data: PrometheusQueryPresetData) -> QueryDefinitionDTO:
        """Convert domain data to query definition DTO."""
        return QueryDefinitionDTO(
            id=data.id,
            name=data.name,
            metric_name=data.metric_name,
            query_template=data.query_template,
            time_window=data.time_window,
            options=QueryDefinitionOptionsDTO(
                filter_labels=data.filter_labels,
                group_labels=data.group_labels,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )

    def convert_metric_response(self, response: MetricResponse) -> QueryDefinitionMetricResult:
        """Convert a Prometheus MetricResponse to a QueryDefinitionMetricResult DTO."""
        metric_labels = [
            MetricLabelEntryDTO(key=key, value=str(val))
            for key, val in response.metric.model_dump(exclude_none=True).items()
        ]
        values = [MetricValueDTO(timestamp=ts, value=v) for ts, v in response.values]
        return QueryDefinitionMetricResult(metric=metric_labels, values=values)

    def build_updater(
        self, request: ModifyQueryDefinitionRequest, preset_id: UUID
    ) -> Updater[PrometheusQueryPresetRow]:
        """Build an Updater from a modify request."""
        spec = PrometheusQueryPresetUpdaterSpec(
            name=(
                OptionalState.update(request.name)
                if request.name is not None
                else OptionalState.nop()
            ),
            metric_name=(
                OptionalState.update(request.metric_name)
                if request.metric_name is not None
                else OptionalState.nop()
            ),
            query_template=(
                OptionalState.update(request.query_template)
                if request.query_template is not None
                else OptionalState.nop()
            ),
            time_window=TriState.nop()
            if isinstance(request.time_window, Sentinel)
            else TriState.nullify()
            if request.time_window is None
            else TriState.update(request.time_window),
            filter_labels=(
                OptionalState.update(request.options.filter_labels)
                if request.options is not None and request.options.filter_labels is not None
                else OptionalState.nop()
            ),
            group_labels=(
                OptionalState.update(request.options.group_labels)
                if request.options is not None and request.options.group_labels is not None
                else OptionalState.nop()
            ),
        )
        return Updater(spec=spec, pk_value=preset_id)

    def build_querier(self, request: SearchQueryDefinitionsRequest) -> BatchQuerier:
        """Build a BatchQuerier from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        return BatchQuerier(
            conditions=conditions,
            orders=orders,
            pagination=OffsetPagination(limit=request.limit, offset=request.offset),
        )

    def _convert_filter(self, filter_req: QueryDefinitionFilter) -> list[QueryCondition]:
        """Convert query definition filter to list of query conditions."""
        conditions: list[QueryCondition] = []
        if filter_req.name is not None:
            condition = self.convert_string_filter(
                filter_req.name,
                contains_factory=PrometheusQueryPresetConditions.by_name_contains,
                equals_factory=PrometheusQueryPresetConditions.by_name_equals,
                starts_with_factory=PrometheusQueryPresetConditions.by_name_starts_with,
                ends_with_factory=PrometheusQueryPresetConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_order(self, order: QueryDefinitionOrder) -> QueryOrder:
        """Convert query definition order specification to query order."""
        ascending = order.direction == OrderDirection.ASC
        if order.field == QueryDefinitionOrderField.NAME:
            return PrometheusQueryPresetOrders.name(ascending=ascending)
        if order.field == QueryDefinitionOrderField.CREATED_AT:
            return PrometheusQueryPresetOrders.created_at(ascending=ascending)
        if order.field == QueryDefinitionOrderField.UPDATED_AT:
            return PrometheusQueryPresetOrders.updated_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")
