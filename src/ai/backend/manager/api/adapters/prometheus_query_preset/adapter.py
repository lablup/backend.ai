"""Prometheus query preset domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    DeleteQueryDefinitionInput,
    ModifyQueryDefinitionInput,
    ModifyQueryDefinitionOptionsInput,
    PreviewQueryDefinitionInput,
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
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
    PrometheusQueryPresetData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreator,
)
from ai.backend.manager.models.prometheus_query_preset.scopes import (
    PublicPrometheusQueryPresetTarget,
)
from ai.backend.manager.models.prometheus_query_preset.searchable_fields import (
    PrometheusQueryPresetSearchableFields,
)
from ai.backend.manager.models.prometheus_query_preset.searchers import (
    PrometheusQueryPresetSearcher,
)
from ai.backend.manager.models.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdater,
)
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.services.prometheus_query_preset.actions.bulk_get import (
    BulkGetPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.create import CreatePresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.execute_preset import (
    ExecutePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.get import GetPresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.preview import (
    PreviewPresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.purge import PurgePresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.scoped_search import (
    ScopedSearchPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.update import UpdatePresetAction
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.types import OptionalState, TriState


class PrometheusQueryPresetAdapter(BaseAdapter):
    """Adapter for prometheus query preset domain operations."""

    _prometheus_query_preset: PrometheusQueryPresetProcessors

    def __init__(self, prometheus_query_preset: PrometheusQueryPresetProcessors) -> None:
        self._prometheus_query_preset = prometheus_query_preset

    async def batch_load_by_ids(
        self, ids: Sequence[PrometheusQueryPresetID]
    ) -> list[QueryDefinitionNode | Exception | None]:
        """Batch load presets by id for DataLoader use.

        One answer per id in the given order: the node, ``None`` for an id matching no
        row, and the denial for one the caller may not read.
        """
        if not ids:
            return []
        result = await self._prometheus_query_preset.bulk_get_presets.run(
            BulkGetPresetsAction(ids=list(ids))
        )
        return [
            self._data_to_dto(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

    async def create(self, input: CreateQueryDefinitionInput) -> CreateQueryDefinitionPayload:
        """Create a new prometheus query definition."""
        creator = PrometheusQueryPresetCreator(
            name=input.name,
            description=input.description,
            rank=input.rank,
            category_id=(
                PrometheusQueryPresetCategoryID(input.category_id)
                if input.category_id is not None
                else None
            ),
            metric_name=input.metric_name,
            query_template=input.query_template,
            time_window=input.time_window,
            filter_labels=input.options.filter_labels,
            group_labels=input.options.group_labels,
        )

        action_result = await self._prometheus_query_preset.global_create_preset.run(
            CreatePresetAction(creator=creator)
        )

        return CreateQueryDefinitionPayload(item=self._data_to_dto(action_result.data))

    async def search(self, input: SearchQueryDefinitionsInput) -> SearchQueryDefinitionsPayload:
        """Search prometheus query presets.

        Available to any authenticated user via REST/GQL — presets are a
        shared catalog of metric query templates.
        """
        searcher = self.build_searcher(input)

        action_result = await self._prometheus_query_preset.scoped_search_presets.run(
            self._scoped_search(searcher)
        )

        return SearchQueryDefinitionsPayload(
            items=[self._data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, preset_id: UUID) -> GetQueryDefinitionPayload:
        """Get a single query definition by ID."""
        action_result = await self._prometheus_query_preset.get_preset.run(
            GetPresetAction(preset_id=PrometheusQueryPresetID(preset_id))
        )

        return GetQueryDefinitionPayload(item=self._data_to_dto(action_result.data))

    async def update(
        self, preset_id: UUID, input: ModifyQueryDefinitionInput
    ) -> ModifyQueryDefinitionPayload:
        """Update an existing query definition."""
        action_result = await self._prometheus_query_preset.update_preset.run(
            UpdatePresetAction(
                updater=self._build_updater(PrometheusQueryPresetID(preset_id), input)
            )
        )

        return ModifyQueryDefinitionPayload(item=self._data_to_dto(action_result.preset))

    async def admin_preview(self, input: PreviewQueryDefinitionInput) -> QueryDefinitionResultInfo:
        """Preview a prometheus query template (admin only)."""
        action_result = await self._prometheus_query_preset.global_preview_preset.run(
            PreviewPresetAction(query_template=input.query_template)
        )
        return self._prometheus_response_to_result_info(action_result.response)

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
        action_result = await self._prometheus_query_preset.execute_preset.run(
            ExecutePresetAction(
                preset_id=PrometheusQueryPresetID(preset_id),
                options=execute_options,
                time_window=time_window,
                time_range=qtr,
            )
        )
        return self._prometheus_response_to_result_info(action_result.response)

    def _prometheus_response_to_result_info(
        self,
        response: PrometheusResponse,
    ) -> QueryDefinitionResultInfo:
        """Convert a raw Prometheus response into the manager-layer DTO."""
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
        action_result = await self._prometheus_query_preset.purge_preset.run(
            PurgePresetAction(preset_id=PrometheusQueryPresetID(input.id))
        )

        return DeleteQueryDefinitionPayload(id=action_result.data.id)

    _PAGINATION_SPEC = PaginationSpec(
        forward_order=PrometheusQueryPresetSearchableFields.own.created_at.order.apply(
            ascending=False
        ),
        cursor_column=PrometheusQueryPresetRow.id,
    )

    def build_searcher(self, input: SearchQueryDefinitionsInput) -> PrometheusQueryPresetSearcher:
        """Build the searcher from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        return self._build_searcher(
            PrometheusQueryPresetSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=self._PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

    def _scoped_search(self, searcher: PrometheusQueryPresetSearcher) -> ScopedSearchPresetsAction:
        return ScopedSearchPresetsAction(
            searcher=ScopedSearcher(
                scopes=[PublicPrometheusQueryPresetTarget()], used_by=(), searcher=searcher
            )
        )

    def _convert_filter(self, filter: QueryDefinitionFilter) -> list[QueryCondition]:
        fields = PrometheusQueryPresetSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_string_filter(filter.name, fields.name.filter),
            *self.apply_uuid_filter(filter.category_id, fields.category_id.filter),
        ]

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))

        if filter.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_sub_conditions.extend(self._convert_filter(sub_filter))
            if or_sub_conditions:
                conditions.append(combine_conditions_or(or_sub_conditions))

        if filter.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_sub_conditions.extend(self._convert_filter(sub_filter))
            if not_sub_conditions:
                conditions.append(negate_conditions(not_sub_conditions))

        return conditions

    def _convert_orders(self, orders: list[QueryDefinitionOrder]) -> list[QueryOrder]:
        fields = PrometheusQueryPresetSearchableFields.own
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "name":
                    result.append(fields.name.order.apply(ascending))
                case "rank":
                    result.append(fields.rank.order.apply(ascending))
                case "created_at":
                    result.append(fields.created_at.order.apply(ascending))
                case "updated_at":
                    result.append(fields.updated_at.order.apply(ascending))
        return result

    @staticmethod
    def _build_updater(
        preset_id: PrometheusQueryPresetID, input: ModifyQueryDefinitionInput
    ) -> PrometheusQueryPresetUpdater:
        options = OptionalState[ModifyQueryDefinitionOptionsInput].from_unset(input.options)
        return PrometheusQueryPresetUpdater(
            preset_id=preset_id,
            name=OptionalState.from_unset(input.name),
            description=TriState.from_unset(input.description),
            rank=OptionalState.from_unset(input.rank),
            category_id=TriState.from_unset(input.category_id),
            metric_name=OptionalState.from_unset(input.metric_name),
            query_template=OptionalState.from_unset(input.query_template),
            time_window=TriState.from_unset(input.time_window),
            filter_labels=options.and_optional(lambda o: o.filter_labels),
            group_labels=options.and_optional(lambda o: o.group_labels),
        )

    @staticmethod
    def _data_to_dto(data: PrometheusQueryPresetData) -> QueryDefinitionNode:
        """Convert data layer type to Pydantic DTO."""
        return QueryDefinitionNode(
            id=data.id,
            entity_id=data.entity_id(),
            name=data.name,
            description=data.description,
            rank=data.rank,
            category_id=data.category_id,
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
