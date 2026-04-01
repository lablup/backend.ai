from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
    RuntimeVariantPresetFilter,
    RuntimeVariantPresetOrder,
    SearchRuntimeVariantPresetsInput,
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    CreateRuntimeVariantPresetPayload,
    DeleteRuntimeVariantPresetPayload,
    RuntimeVariantPresetNode,
    SearchRuntimeVariantPresetsPayload,
    UpdateRuntimeVariantPresetPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    RuntimeVariantPresetOrderField,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.errors.resource import RuntimeVariantPresetNotFound
from ai.backend.manager.models.runtime_variant_preset.conditions import (
    RuntimeVariantPresetConditions,
)
from ai.backend.manager.models.runtime_variant_preset.orders import RuntimeVariantPresetOrders
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, combine_conditions_or
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.runtime_variant_preset.creators import (
    RuntimeVariantPresetCreatorSpec,
)
from ai.backend.manager.repositories.runtime_variant_preset.updaters import (
    RuntimeVariantPresetUpdaterSpec,
)
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.delete import (
    DeleteRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.search import (
    SearchRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RuntimeVariantPresetOrders.rank(ascending=True),
        backward_order=RuntimeVariantPresetOrders.rank(ascending=False),
        forward_condition_factory=RuntimeVariantPresetConditions.by_cursor_forward,
        backward_condition_factory=RuntimeVariantPresetConditions.by_cursor_backward,
        tiebreaker_order=RuntimeVariantPresetRow.id.asc(),
    )


class RuntimeVariantPresetAdapter(BaseAdapter):
    async def search(
        self,
        input: SearchRuntimeVariantPresetsInput,
    ) -> SearchRuntimeVariantPresetsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_preset_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._processors.runtime_variant_preset.search.wait_for_complete(
            SearchRuntimeVariantPresetsAction(querier=querier)
        )
        return SearchRuntimeVariantPresetsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, preset_id: UUID) -> RuntimeVariantPresetNode:
        conditions: list[QueryCondition] = [lambda: RuntimeVariantPresetRow.id == preset_id]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_preset_pagination_spec(),
            limit=1,
        )
        result = await self._processors.runtime_variant_preset.search.wait_for_complete(
            SearchRuntimeVariantPresetsAction(querier=querier)
        )
        if not result.items:
            raise RuntimeVariantPresetNotFound()
        return self._data_to_node(result.items[0])

    async def create(
        self,
        input: CreateRuntimeVariantPresetInput,
    ) -> CreateRuntimeVariantPresetPayload:
        creator = Creator(
            spec=RuntimeVariantPresetCreatorSpec(
                runtime_variant_id=input.runtime_variant_id,
                name=input.name,
                description=input.description,
                rank=0,
                preset_target=input.preset_target.value,
                value_type=input.value_type.value,
                default_value=input.default_value,
                key=input.key,
            )
        )
        result = await self._processors.runtime_variant_preset.create.wait_for_complete(
            CreateRuntimeVariantPresetAction(creator=creator)
        )
        return CreateRuntimeVariantPresetPayload(preset=self._data_to_node(result.preset))

    async def update(
        self,
        input: UpdateRuntimeVariantPresetInput,
    ) -> UpdateRuntimeVariantPresetPayload:
        spec = RuntimeVariantPresetUpdaterSpec(
            name=(
                OptionalState.update(input.name) if input.name is not None else OptionalState.nop()
            ),
            description=(
                TriState.nop()
                if input.description is SENTINEL
                else TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
            rank=(
                OptionalState.update(input.rank) if input.rank is not None else OptionalState.nop()
            ),
            preset_target=(
                OptionalState.update(input.preset_target.value)
                if input.preset_target is not None
                else OptionalState.nop()
            ),
            value_type=(
                OptionalState.update(input.value_type.value)
                if input.value_type is not None
                else OptionalState.nop()
            ),
            default_value=(
                TriState.nop()
                if input.default_value is SENTINEL
                else TriState.nullify()
                if input.default_value is None
                else TriState.update(input.default_value)
            ),
            key=(OptionalState.update(input.key) if input.key is not None else OptionalState.nop()),
        )
        updater: Updater[RuntimeVariantPresetRow] = Updater(spec=spec, pk_value=input.id)
        result = await self._processors.runtime_variant_preset.update.wait_for_complete(
            UpdateRuntimeVariantPresetAction(id=input.id, updater=updater)
        )
        return UpdateRuntimeVariantPresetPayload(preset=self._data_to_node(result.preset))

    async def delete(self, preset_id: UUID) -> DeleteRuntimeVariantPresetPayload:
        result = await self._processors.runtime_variant_preset.delete.wait_for_complete(
            DeleteRuntimeVariantPresetAction(id=preset_id)
        )
        return DeleteRuntimeVariantPresetPayload(id=result.preset.id)

    def _convert_filter(self, filter_: RuntimeVariantPresetFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter_.runtime_variant_id is not None:
            conditions.append(
                RuntimeVariantPresetConditions.by_runtime_variant_id(filter_.runtime_variant_id)
            )
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=RuntimeVariantPresetConditions.by_name_contains,
                equals_factory=RuntimeVariantPresetConditions.by_name_equals,
                starts_with_factory=RuntimeVariantPresetConditions.by_name_starts_with,
                ends_with_factory=RuntimeVariantPresetConditions.by_name_ends_with,
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
        return conditions

    def _convert_orders(self, orders: list[RuntimeVariantPresetOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction.value == "ASC"
            match order.field:
                case RuntimeVariantPresetOrderField.NAME:
                    result.append(RuntimeVariantPresetOrders.name(ascending))
                case RuntimeVariantPresetOrderField.RANK:
                    result.append(RuntimeVariantPresetOrders.rank(ascending))
                case RuntimeVariantPresetOrderField.CREATED_AT:
                    result.append(RuntimeVariantPresetOrders.created_at(ascending))
        return result

    @staticmethod
    def _data_to_node(data: RuntimeVariantPresetData) -> RuntimeVariantPresetNode:
        return RuntimeVariantPresetNode(
            id=data.id,
            runtime_variant_id=data.runtime_variant_id,
            name=data.name,
            description=data.description,
            rank=data.rank,
            preset_target=data.preset_target,
            value_type=data.value_type,
            default_value=data.default_value,
            key=data.key,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
