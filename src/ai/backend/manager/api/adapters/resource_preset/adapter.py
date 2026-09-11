"""Resource preset adapter bridging DTOs and Processors."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    ResourceSlotEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
    ResourcePresetFilter,
    ResourcePresetOrder,
    UpdateResourcePresetInput,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    AdminSearchResourcePresetsPayload,
    CreateResourcePresetPayload,
    DeleteResourcePresetPayload,
    ResourcePresetNode,
    UpdateResourcePresetPayload,
)
from ai.backend.common.dto.manager.v2.resource_preset.types import (
    ResourcePresetOrderDirection,
    ResourcePresetOrderField,
)
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.resource_preset.conditions import ResourcePresetConditions
from ai.backend.manager.models.resource_preset.creators import ResourcePresetCreator
from ai.backend.manager.models.resource_preset.orders import ResourcePresetOrders
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.updaters import ResourcePresetUpdater
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.get_preset import (
    GetResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.search_presets import (
    SearchResourcePresetsV2Action,
)
from ai.backend.manager.services.resource_preset.actions.update_preset import (
    UpdateResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.types import OptionalState, TriState


def _resolve_binary_size_input(input: BinarySizeInput | None) -> int | None:
    """Resolve BinarySizeInput to bytes integer."""
    if input is None:
        return None
    return input.bytes


def _resource_slot_entries_to_slot(
    entries: list[Any],
) -> ResourceSlot:
    """Convert list of ResourceSlotEntryInput to ResourceSlot dict."""
    return ResourceSlot({e.resource_type: Decimal(e.quantity) for e in entries})


def _resource_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ResourcePresetOrders.name(ascending=True),
        backward_order=ResourcePresetOrders.name(ascending=False),
        forward_condition_factory=ResourcePresetConditions.by_cursor_forward,
        backward_condition_factory=ResourcePresetConditions.by_cursor_backward,
        tiebreaker_order=ResourcePresetRow.name.asc(),
    )


class ResourcePresetAdapter(BaseAdapter):
    """Adapter for resource preset operations."""

    _resource_preset: ResourcePresetProcessors

    def __init__(self, resource_preset: ResourcePresetProcessors) -> None:
        self._resource_preset = resource_preset

    async def search(
        self,
        input: AdminSearchResourcePresetsInput,
    ) -> AdminSearchResourcePresetsPayload:
        """Search resource presets with filters, ordering, and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination_spec = _resource_preset_pagination_spec()
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=pagination_spec,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        result = await self._resource_preset.search_presets_v2.run(
            SearchResourcePresetsV2Action(querier=querier)
        )
        return AdminSearchResourcePresetsPayload(
            items=[self._data_to_node(p) for p in result.presets],
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def get(self, preset_id: UUID) -> ResourcePresetNode:
        """Get a single resource preset by ID."""
        try:
            result = await self._resource_preset.get_preset.run(
                GetResourcePresetAction(preset_id=ResourcePresetID(preset_id))
            )
        except NotFoundError as e:
            # The generic repository names no domain; the route answered with the
            # preset's own error before and keeps doing so.
            raise ResourcePresetNotFound() from e
        return self._data_to_node(result.data)

    async def create(
        self,
        name: str,
        resource_slots: ResourceSlot,
        shared_memory: int | None,
        resource_group_name: str | None,
    ) -> CreateResourcePresetPayload:
        """Create a new resource preset."""
        shared_memory_str = str(shared_memory) if shared_memory is not None else None
        creator = ResourcePresetCreator(
            name=name,
            resource_slots=resource_slots,
            shared_memory=shared_memory_str,
            resource_group_name=resource_group_name,
        )
        result = await self._resource_preset.create_preset.run(
            CreateResourcePresetAction(creator=creator)
        )
        return CreateResourcePresetPayload(
            resource_preset=self._data_to_node(result.resource_preset),
        )

    async def update(
        self,
        input: UpdateResourcePresetInput,
    ) -> UpdateResourcePresetPayload:
        """Update an existing resource preset."""
        updater = ResourcePresetUpdater(
            preset_id=ResourcePresetID(input.id),
            resource_slots=OptionalState.from_unset(input.resource_slots).map(
                _resource_slot_entries_to_slot
            ),
            name=OptionalState.from_unset(input.name),
            shared_memory=TriState.from_unset(input.shared_memory).map(
                lambda v: BinarySize(v.bytes)
            ),
            resource_group_name=TriState.from_unset(input.resource_group_name),
        )
        result = await self._resource_preset.update_preset.run(
            UpdateResourcePresetAction(updater=updater)
        )
        return UpdateResourcePresetPayload(
            resource_preset=self._data_to_node(result.resource_preset),
        )

    async def delete(self, preset_id: UUID) -> DeleteResourcePresetPayload:
        """Delete a resource preset by ID."""
        result = await self._resource_preset.delete_preset.run(
            DeleteResourcePresetAction(preset_id=ResourcePresetID(preset_id))
        )
        return DeleteResourcePresetPayload(id=result.resource_preset.id)

    def _convert_filter(self, filter_: ResourcePresetFilter) -> list[QueryCondition]:
        """Convert ResourcePresetFilter DTO to QueryConditions."""
        conditions: list[QueryCondition] = []
        if filter_.name:
            cond = self.convert_string_filter(
                filter_.name,
                contains_factory=ResourcePresetConditions.by_name_contains,
                equals_factory=ResourcePresetConditions.by_name_equals,
                starts_with_factory=ResourcePresetConditions.by_name_starts_with,
                ends_with_factory=ResourcePresetConditions.by_name_ends_with,
                in_factory=ResourcePresetConditions.by_name_in,
            )
            if cond:
                conditions.append(cond)
        if filter_.resource_group_name:
            cond = self.convert_string_filter(
                filter_.resource_group_name,
                contains_factory=ResourcePresetConditions.by_resource_group_name_contains,
                equals_factory=ResourcePresetConditions.by_resource_group_name_equals,
                starts_with_factory=ResourcePresetConditions.by_resource_group_name_starts_with,
                ends_with_factory=ResourcePresetConditions.by_resource_group_name_ends_with,
                in_factory=ResourcePresetConditions.by_resource_group_name_in,
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

    def _convert_orders(self, orders: list[ResourcePresetOrder]) -> list[Any]:
        """Convert ResourcePresetOrder DTOs to QueryOrders."""
        result = []
        for order in orders:
            ascending = order.direction == ResourcePresetOrderDirection.ASC
            match order.field:
                case ResourcePresetOrderField.NAME:
                    result.append(ResourcePresetOrders.name(ascending))
        return result

    @staticmethod
    def _data_to_node(data: ResourcePresetData) -> ResourcePresetNode:
        """Convert ResourcePresetData to ResourcePresetNode DTO."""
        return ResourcePresetNode(
            id=data.id,
            name=data.name,
            resource_slots=[
                ResourceSlotEntryInfo(resource_type=k, quantity=v)
                for k, v in data.resource_slots.items()
            ],
            shared_memory=(
                BinarySize.to_size_info(data.shared_memory)
                if data.shared_memory is not None
                else None
            ),
            resource_group_name=data.resource_group_name,
        )
