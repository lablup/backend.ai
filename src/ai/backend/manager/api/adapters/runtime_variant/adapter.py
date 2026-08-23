from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput,
    DeleteRuntimeVariantsInput,
    RuntimeVariantFilter,
    RuntimeVariantOrder,
    SearchRuntimeVariantsInput,
    UpdateRuntimeVariantInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import (
    CreateRuntimeVariantPayload,
    DeleteRuntimeVariantPayload,
    DeleteRuntimeVariantsPayload,
    RuntimeVariantModelDefinitionInfo,
    RuntimeVariantNode,
    SearchRuntimeVariantsPayload,
    UpdateRuntimeVariantPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.runtime_variant.conditions import RuntimeVariantConditions
from ai.backend.manager.models.runtime_variant.creators import RuntimeVariantCreator
from ai.backend.manager.models.runtime_variant.orders import RuntimeVariantOrders
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant.searchers import RuntimeVariantSearcher
from ai.backend.manager.models.runtime_variant.updaters import RuntimeVariantUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.services.runtime_variant.actions.create import CreateRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.get import GetRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.lookup import (
    LookupRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.purge import PurgeRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.search import SearchRuntimeVariantsAction
from ai.backend.manager.services.runtime_variant.actions.update import UpdateRuntimeVariantAction
from ai.backend.manager.types import OptionalState, TriState


def _runtime_variant_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RuntimeVariantOrders.created_at(ascending=False),
        backward_order=RuntimeVariantOrders.created_at(ascending=True),
        forward_condition_factory=RuntimeVariantConditions.by_cursor_forward,
        backward_condition_factory=RuntimeVariantConditions.by_cursor_backward,
        tiebreaker_order=RuntimeVariantRow.name.asc(),
    )


class RuntimeVariantAdapter(BaseAdapter):
    async def batch_load_by_ids(self, ids: Sequence[UUID]) -> list[RuntimeVariantNode | None]:
        if not ids:
            return []
        searcher = RuntimeVariantSearcher(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[RuntimeVariantConditions.by_ids(ids)],
        )
        result = await self._processors.runtime_variant.public_search.run(
            SearchRuntimeVariantsAction(searcher=searcher)
        )
        variant_map = {item.id: self._data_to_node(item) for item in result.items}
        return [variant_map.get(RuntimeVariantID(variant_id)) for variant_id in ids]

    async def search(
        self,
        input: SearchRuntimeVariantsInput,
    ) -> SearchRuntimeVariantsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        searcher = self._build_searcher(
            RuntimeVariantSearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=_runtime_variant_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.runtime_variant.public_search.run(
            SearchRuntimeVariantsAction(searcher=searcher)
        )
        return SearchRuntimeVariantsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, variant_id: UUID) -> RuntimeVariantNode:
        result = await self._processors.runtime_variant.public_get.run(
            GetRuntimeVariantAction(variant_id=RuntimeVariantID(variant_id))
        )
        return self._data_to_node(result.data)

    async def create(
        self,
        input: CreateRuntimeVariantInput,
    ) -> CreateRuntimeVariantPayload:
        creator = RuntimeVariantCreator(
            name=input.name,
            description=input.description,
        )
        result = await self._processors.runtime_variant.global_create.run(
            CreateRuntimeVariantAction(creator=creator)
        )
        return CreateRuntimeVariantPayload(
            runtime_variant=self._data_to_node(result.data),
        )

    async def update(
        self,
        input: UpdateRuntimeVariantInput,
    ) -> UpdateRuntimeVariantPayload:
        updater = RuntimeVariantUpdater(
            variant_id=RuntimeVariantID(input.id),
            name=OptionalState.update(input.name)
            if input.name is not None
            else OptionalState.nop(),
            description=(
                TriState.nop()
                if input.description is SENTINEL
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
        )
        result = await self._processors.runtime_variant.update.run(
            UpdateRuntimeVariantAction(updater=updater)
        )
        return UpdateRuntimeVariantPayload(
            runtime_variant=self._data_to_node(result.data),
        )

    async def delete(self, variant_id: UUID) -> DeleteRuntimeVariantPayload:
        result = await self._processors.runtime_variant.purge.run(
            PurgeRuntimeVariantAction(id=RuntimeVariantID(variant_id))
        )
        return DeleteRuntimeVariantPayload(id=result.data.id)

    async def bulk_delete(self, input: DeleteRuntimeVariantsInput) -> DeleteRuntimeVariantsPayload:
        """Delete multiple runtime variants by ID."""
        for variant_id in input.ids:
            await self._processors.runtime_variant.purge.run(
                PurgeRuntimeVariantAction(id=RuntimeVariantID(variant_id))
            )
        return DeleteRuntimeVariantsPayload(deleted_count=len(input.ids))

    async def resolve_by_name(self, name: str) -> RuntimeVariantID:
        """Resolve a variant name into its ``RuntimeVariantID``.

        Sole entry point used by legacy API handlers to upgrade name-
        carrying inputs before calling id-typed internal adapters. Does
        not form part of the v2 surface — v2 clients pass the id
        directly.
        """
        result = await self._processors.runtime_variant.public_lookup.run(
            LookupRuntimeVariantAction(name=name)
        )
        return result.entity_id()

    def _convert_filter(self, filter_: RuntimeVariantFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=RuntimeVariantConditions.by_name_contains,
                equals_factory=RuntimeVariantConditions.by_name_equals,
                starts_with_factory=RuntimeVariantConditions.by_name_starts_with,
                ends_with_factory=RuntimeVariantConditions.by_name_ends_with,
                in_factory=RuntimeVariantConditions.by_name_in,
            )
            if cond:
                conditions.append(cond)
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                or_conds.extend(self._convert_filter(sub))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            not_conds: list[QueryCondition] = []
            for sub in filter_.NOT:
                not_conds.extend(self._convert_filter(sub))
            if not_conds:
                conditions.append(negate_conditions(not_conds))
        return conditions

    def _convert_orders(self, orders: list[RuntimeVariantOrder]) -> list[QueryOrder]:
        result = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case RuntimeVariantOrderField.NAME:
                    result.append(RuntimeVariantOrders.name(ascending))
                case RuntimeVariantOrderField.CREATED_AT:
                    result.append(RuntimeVariantOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RuntimeVariantData) -> RuntimeVariantNode:
        return RuntimeVariantNode(
            id=data.id,
            name=data.name,
            description=data.description,
            reads_vfolder_config_files=data.reads_vfolder_config_files,
            default_model_definition=RuntimeVariantModelDefinitionInfo.model_validate(
                data.default_model_definition,
                from_attributes=True,
            ),
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
