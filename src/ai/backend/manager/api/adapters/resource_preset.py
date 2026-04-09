"""Resource preset adapter bridging DTOs and Processors."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInfo,
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
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models.resource_preset.conditions import ResourcePresetConditions
from ai.backend.manager.models.resource_preset.orders import ResourcePresetOrders
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.resource_preset.creators import ResourcePresetCreatorSpec
from ai.backend.manager.repositories.resource_preset.updaters import ResourcePresetUpdaterSpec
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.modify_preset import (
    ModifyResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.search_presets import (
    SearchResourcePresetsV2Action,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import BaseAdapter
from .pagination import PaginationSpec


def _humanize_bytes(value: int) -> str:
    """Convert bytes integer to human-readable string (e.g., 1073741824 → '1g')."""
    return f"{BinarySize(value):s}"


def _resolve_binary_size_input(input: BinarySizeInput | None) -> int | None:
    """Resolve BinarySizeInput to bytes integer."""
    if input is None:
        return None
    return input.bytes


def _to_binary_size_info(value: int) -> BinarySizeInfo:
    """Convert bytes integer to BinarySizeInfo DTO."""
    return BinarySizeInfo(value=value, display=_humanize_bytes(value))


def _resource_slot_entries_to_slot(
    entries: list[Any],
) -> ResourceSlot:
    """Convert list of ResourceSlotEntryInput to ResourceSlot dict."""
    return ResourceSlot({e.resource_type: Decimal(e.quantity) for e in entries})


def _resource_preset_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ResourcePresetOrders.id(ascending=False),
        backward_order=ResourcePresetOrders.id(ascending=True),
        forward_condition_factory=ResourcePresetConditions.by_cursor_forward,
        backward_condition_factory=ResourcePresetConditions.by_cursor_backward,
        tiebreaker_order=ResourcePresetRow.name.asc(),
    )


class ResourcePresetAdapter(BaseAdapter):
    """Adapter for resource preset operations."""

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
        result = await self._processors.resource_preset.search_presets_v2.wait_for_complete(
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
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=1),
            conditions=[lambda: ResourcePresetRow.id == preset_id],
        )
        result = await self._processors.resource_preset.search_presets_v2.wait_for_complete(
            SearchResourcePresetsV2Action(querier=querier)
        )
        if not result.presets:
            raise ResourcePresetNotFound()
        return self._data_to_node(result.presets[0])

    async def create(
        self,
        name: str,
        resource_slots: ResourceSlot,
        shared_memory: int | None,
        resource_group_name: str | None,
    ) -> CreateResourcePresetPayload:
        """Create a new resource preset."""
        shared_memory_str = str(shared_memory) if shared_memory is not None else None
        creator = Creator(
            spec=ResourcePresetCreatorSpec(
                name=name,
                resource_slots=resource_slots,
                shared_memory=shared_memory_str,
                scaling_group_name=resource_group_name,
            )
        )
        result = await self._processors.resource_preset.create_preset.wait_for_complete(
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
        resource_slots_state: OptionalState[ResourceSlot] = OptionalState.nop()
        if input.resource_slots is not None:
            resource_slots_state = OptionalState.update(
                _resource_slot_entries_to_slot(input.resource_slots)
            )

        shared_memory_value = _resolve_shared_memory_for_update(input.shared_memory)

        name_state: OptionalState[str] = OptionalState.nop()
        if input.name is not None:
            name_state = OptionalState.update(input.name)

        resource_group_state: TriState[str] = TriState.nop()
        if input.resource_group_name is not SENTINEL:
            if input.resource_group_name is None:
                resource_group_state = TriState.nullify()
            else:
                resource_group_state = TriState.update(input.resource_group_name)

        updater_spec = ResourcePresetUpdaterSpec(
            resource_slots=resource_slots_state,
            name=name_state,
            shared_memory=shared_memory_value,
            scaling_group_name=resource_group_state,
        )
        updater = Updater(spec=updater_spec, pk_value=input.id)
        result = await self._processors.resource_preset.modify_preset.wait_for_complete(
            ModifyResourcePresetAction(updater=updater, id=input.id, name=None)
        )
        return UpdateResourcePresetPayload(
            resource_preset=self._data_to_node(result.resource_preset),
        )

    async def delete(self, preset_id: UUID) -> DeleteResourcePresetPayload:
        """Delete a resource preset by ID."""
        result = await self._processors.resource_preset.delete_preset.wait_for_complete(
            DeleteResourcePresetAction(id=preset_id, name=None)
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
                _to_binary_size_info(data.shared_memory) if data.shared_memory else None
            ),
            resource_group_name=data.scaling_group_name,
        )


def _resolve_shared_memory_for_update(
    shared_memory: BinarySizeInput | object | None,
) -> TriState[BinarySize]:
    """Resolve shared_memory BinarySizeInput for update operations."""
    if shared_memory is SENTINEL:
        return TriState.nop()
    if shared_memory is None:
        return TriState.nullify()
    if not isinstance(shared_memory, BinarySizeInput):
        return TriState.nop()
    return TriState.update(BinarySize(shared_memory.bytes))
