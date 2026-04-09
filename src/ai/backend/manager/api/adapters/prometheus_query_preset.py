"""Prometheus query preset domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    DeleteQueryDefinitionInput,
    ModifyQueryDefinitionInput,
    QueryDefinitionFilter,
    QueryDefinitionOrder,
    QueryTimeRangeInputDTO,
    SearchQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    ExecuteQueryDefinitionOptionsInput as ExecuteQueryDefinitionOptionsInputDTO,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    GetQueryDefinitionPayload,
    ModifyQueryDefinitionPayload,
    QueryDefinitionMetricResultInfo,
    QueryDefinitionNode,
    QueryDefinitionResultInfo,
    SearchQueryDefinitionsPayload,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import (
    MetricLabelEntryInfo,
    MetricValueInfo,
    OrderDirection,
    QueryDefinitionOptionsInfo,
)
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
    PrometheusQueryPresetData,
)
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.conditions import (
    PrometheusQueryPresetConditions,
)
from ai.backend.manager.models.prometheus_query_preset.orders import PrometheusQueryPresetOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
    Updater,
)
from ai.backend.manager.repositories.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreatorSpec,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    DeletePresetAction,
    ExecutePresetAction,
    GetPresetAction,
    ModifyPresetAction,
    SearchPresetsAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class PrometheusQueryPresetAdapter(BaseAdapter):
    """Adapter for prometheus query preset domain operations."""

    async def create(self, input: CreateQueryDefinitionInput) -> CreateQueryDefinitionPayload:
        """Create a new prometheus query definition."""
        creator: Creator[PrometheusQueryPresetRow] = Creator(
            spec=PrometheusQueryPresetCreatorSpec(
                name=input.name,
                metric_name=input.metric_name,
                query_template=input.query_template,
                time_window=input.time_window,
                filter_labels=input.options.filter_labels,
                group_labels=input.options.group_labels,
            )
        )

        action_result = (
            await self._processors.prometheus_query_preset.create_preset.wait_for_complete(
                CreatePresetAction(creator=creator)
            )
        )

        return CreateQueryDefinitionPayload(item=self._data_to_dto(action_result.preset))

    async def search(self, input: SearchQueryDefinitionsInput) -> SearchQueryDefinitionsPayload:
        """Search prometheus query presets.

        Available to any authenticated user via REST/GQL — presets are a
        shared catalog of metric query templates.
        """
        querier = self.build_querier(input)

        action_result = (
            await self._processors.prometheus_query_preset.search_presets.wait_for_complete(
                SearchPresetsAction(querier=querier)
            )
        )

        return SearchQueryDefinitionsPayload(
            items=[self._data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, preset_id: UUID) -> GetQueryDefinitionPayload:
        """Get a single query definition by ID."""
        action_result = await self._processors.prometheus_query_preset.get_preset.wait_for_complete(
            GetPresetAction(preset_id=preset_id)
        )

        return GetQueryDefinitionPayload(item=self._data_to_dto(action_result.preset))

    async def update(
        self, preset_id: UUID, input: ModifyQueryDefinitionInput
    ) -> ModifyQueryDefinitionPayload:
        """Update an existing query definition."""
        updater: Updater[PrometheusQueryPresetRow] = Updater(
            spec=self._build_updater_spec(input),
            pk_value=preset_id,
        )

        action_result = (
            await self._processors.prometheus_query_preset.modify_preset.wait_for_complete(
                ModifyPresetAction(preset_id=preset_id, updater=updater)
            )
        )

        return ModifyQueryDefinitionPayload(item=self._data_to_dto(action_result.preset))

    async def execute_preset(
        self,
        preset_id: UUID,
        options: ExecuteQueryDefinitionOptionsInputDTO | None,
        time_window: str | None,
        time_range: QueryTimeRangeInputDTO | None,
    ) -> QueryDefinitionResultInfo:
        """Execute a query definition and return the result as a manager DTO."""
        execute_options = ExecutePresetOptions(
            filter_labels={e.key: e.value for e in (options.filter_labels or [])}
            if options is not None
            else {},
            group_labels=(options.group_labels or []) if options is not None else [],
        )
        qtr = (
            QueryTimeRange(
                start=time_range.start.isoformat(),
                end=time_range.end.isoformat(),
                step=time_range.step,
            )
            if time_range is not None
            else None
        )
        action_result = (
            await self._processors.prometheus_query_preset.execute_preset.wait_for_complete(
                ExecutePresetAction(
                    preset_id=preset_id,
                    options=execute_options,
                    time_window=time_window,
                    time_range=qtr,
                )
            )
        )
        response = action_result.response
        return QueryDefinitionResultInfo(
            status=response.status,
            result_type=response.data.result_type,
            result=[
                QueryDefinitionMetricResultInfo(
                    metric=[
                        MetricLabelEntryInfo(key=k, value=v)
                        for k, v in mr.metric.model_dump(exclude_none=True).items()
                    ],
                    values=[MetricValueInfo(timestamp=ts, value=val) for ts, val in mr.values],
                )
                for mr in response.data.result
            ],
        )

    async def delete(self, input: DeleteQueryDefinitionInput) -> DeleteQueryDefinitionPayload:
        """Delete a query definition by ID."""
        action_result = (
            await self._processors.prometheus_query_preset.delete_preset.wait_for_complete(
                DeletePresetAction(preset_id=input.id)
            )
        )

        return DeleteQueryDefinitionPayload(id=action_result.preset_id)

    def build_querier(self, input: SearchQueryDefinitionsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: QueryDefinitionFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=PrometheusQueryPresetConditions.by_name_contains,
                equals_factory=PrometheusQueryPresetConditions.by_name_equals,
                starts_with_factory=PrometheusQueryPresetConditions.by_name_starts_with,
                ends_with_factory=PrometheusQueryPresetConditions.by_name_ends_with,
                in_factory=PrometheusQueryPresetConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    @staticmethod
    def _convert_orders(orders: list[QueryDefinitionOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "name":
                    result.append(PrometheusQueryPresetOrders.name(ascending))
                case "created_at":
                    result.append(PrometheusQueryPresetOrders.created_at(ascending))
                case "updated_at":
                    result.append(PrometheusQueryPresetOrders.updated_at(ascending))
        return result

    @staticmethod
    def _build_pagination(input: SearchQueryDefinitionsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _build_updater_spec(input: ModifyQueryDefinitionInput) -> PrometheusQueryPresetUpdaterSpec:
        return PrometheusQueryPresetUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            metric_name=(
                OptionalState.update(input.metric_name)
                if input.metric_name is not None
                else OptionalState.nop()
            ),
            query_template=(
                OptionalState.update(input.query_template)
                if input.query_template is not None
                else OptionalState.nop()
            ),
            time_window=TriState.nop()
            if isinstance(input.time_window, Sentinel)
            else TriState.nullify()
            if input.time_window is None
            else TriState.update(input.time_window),
            filter_labels=(
                OptionalState.update(input.options.filter_labels)
                if input.options is not None and input.options.filter_labels is not None
                else OptionalState.nop()
            ),
            group_labels=(
                OptionalState.update(input.options.group_labels)
                if input.options is not None and input.options.group_labels is not None
                else OptionalState.nop()
            ),
        )

    @staticmethod
    def _data_to_dto(data: PrometheusQueryPresetData) -> QueryDefinitionNode:
        """Convert data layer type to Pydantic DTO."""
        return QueryDefinitionNode(
            id=data.id,
            name=data.name,
            metric_name=data.metric_name,
            query_template=data.query_template,
            time_window=data.time_window,
            options=QueryDefinitionOptionsInfo(
                filter_labels=data.filter_labels,
                group_labels=data.group_labels,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
