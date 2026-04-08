from __future__ import annotations

from uuid import UUID

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
    RuntimeVariantNode,
    SearchRuntimeVariantsPayload,
    UpdateRuntimeVariantPayload,
)
from ai.backend.common.dto.manager.v2.runtime_variant.types import RuntimeVariantOrderField
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.errors.resource import RuntimeVariantNotFound
from ai.backend.manager.models.runtime_variant.conditions import RuntimeVariantConditions
from ai.backend.manager.models.runtime_variant.orders import RuntimeVariantOrders
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, combine_conditions_or
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.runtime_variant.creators import RuntimeVariantCreatorSpec
from ai.backend.manager.repositories.runtime_variant.updaters import RuntimeVariantUpdaterSpec
from ai.backend.manager.services.runtime_variant.actions.create import CreateRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.delete import DeleteRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.search import SearchRuntimeVariantsAction
from ai.backend.manager.services.runtime_variant.actions.update import UpdateRuntimeVariantAction
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter


def _runtime_variant_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RuntimeVariantOrders.id(ascending=False),
        backward_order=RuntimeVariantOrders.id(ascending=True),
        forward_condition_factory=RuntimeVariantConditions.by_cursor_forward,
        backward_condition_factory=RuntimeVariantConditions.by_cursor_backward,
        tiebreaker_order=RuntimeVariantRow.name.asc(),
    )


class RuntimeVariantAdapter(BaseAdapter):
    async def search(
        self,
        input: SearchRuntimeVariantsInput,
    ) -> SearchRuntimeVariantsPayload:
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
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
        result = await self._processors.runtime_variant.search.wait_for_complete(
            SearchRuntimeVariantsAction(querier=querier)
        )
        return SearchRuntimeVariantsPayload(
            items=[self._data_to_node(d) for d in result.items],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, variant_id: UUID) -> RuntimeVariantNode:
        conditions: list[QueryCondition] = [lambda: RuntimeVariantRow.id == variant_id]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_runtime_variant_pagination_spec(),
            limit=1,
        )
        result = await self._processors.runtime_variant.search.wait_for_complete(
            SearchRuntimeVariantsAction(querier=querier)
        )
        if not result.items:
            raise RuntimeVariantNotFound()
        return self._data_to_node(result.items[0])

    async def create(
        self,
        input: CreateRuntimeVariantInput,
    ) -> CreateRuntimeVariantPayload:
        creator = Creator(
            spec=RuntimeVariantCreatorSpec(
                name=input.name,
                description=input.description,
            )
        )
        result = await self._processors.runtime_variant.create.wait_for_complete(
            CreateRuntimeVariantAction(creator=creator)
        )
        return CreateRuntimeVariantPayload(
            runtime_variant=self._data_to_node(result.runtime_variant),
        )

    async def update(
        self,
        input: UpdateRuntimeVariantInput,
    ) -> UpdateRuntimeVariantPayload:
        spec = RuntimeVariantUpdaterSpec(
            name=OptionalState.update(input.name)
            if input.name is not None
            else OptionalState.nop(),
            description=(
                TriState.nullify()
                if input.description is None
                else TriState.update(input.description)
            ),
        )
        updater: Updater[RuntimeVariantRow] = Updater(spec=spec, pk_value=input.id)
        result = await self._processors.runtime_variant.update.wait_for_complete(
            UpdateRuntimeVariantAction(id=input.id, updater=updater)
        )
        return UpdateRuntimeVariantPayload(
            runtime_variant=self._data_to_node(result.runtime_variant),
        )

    async def delete(self, variant_id: UUID) -> DeleteRuntimeVariantPayload:
        result = await self._processors.runtime_variant.delete.wait_for_complete(
            DeleteRuntimeVariantAction(id=variant_id)
        )
        return DeleteRuntimeVariantPayload(id=result.runtime_variant.id)

    async def bulk_delete(self, input: DeleteRuntimeVariantsInput) -> DeleteRuntimeVariantsPayload:
        """Delete multiple runtime variants by ID."""
        for variant_id in input.ids:
            await self._processors.runtime_variant.delete.wait_for_complete(
                DeleteRuntimeVariantAction(id=variant_id)
            )
        return DeleteRuntimeVariantsPayload(deleted_count=len(input.ids))

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
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
