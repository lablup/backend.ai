"""Resource preset adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    PartialBulkFailure,
    PartialBulkPayload,
    ResourceSlotEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
    PartialBulkPurgeResourcePresetsInput,
    PartialBulkUpdateResourcePresetItemInput,
    PartialBulkUpdateResourcePresetsInput,
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
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.tristate.unset import Unset
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.actions.v2.bulk.result import PartialBulkResult
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.errors.base.not_found import NotFoundError
from ai.backend.manager.errors.resource import ResourcePresetNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import (
    combine_conditions_and,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.models.resource_preset.creators import ResourcePresetCreator
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.searchable_fields import (
    ResourcePresetSearchableFields,
)
from ai.backend.manager.models.resource_preset.searchers import ResourcePresetSearcher
from ai.backend.manager.models.resource_preset.updaters import ResourcePresetUpdater
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_preset.actions.bulk_get import (
    BulkGetResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.get_preset import (
    GetResourcePresetAction,
)
from ai.backend.manager.services.resource_preset.actions.partial_bulk_purge_presets import (
    PartialBulkPurgeResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.partial_bulk_update_presets import (
    PartialBulkUpdateResourcePresetsAction,
)
from ai.backend.manager.services.resource_preset.actions.search_presets import (
    SearchResourcePresetsV2Action,
)
from ai.backend.manager.services.resource_preset.actions.set_preset_resource_group import (
    SetResourcePresetResourceGroupAction,
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
        forward_order=ResourcePresetSearchableFields.own.name.order.apply(ascending=True),
        cursor_column=ResourcePresetRow.id,
    )


class ResourcePresetAdapter(BaseAdapter):
    """Adapter for resource preset operations."""

    _resource_preset: ResourcePresetProcessors
    _resource_group: ResourceGroupProcessors

    def __init__(
        self,
        resource_preset: ResourcePresetProcessors,
        resource_group: ResourceGroupProcessors,
    ) -> None:
        self._resource_preset = resource_preset
        self._resource_group = resource_group

    async def _resource_group_id(self, name: str | None) -> ResourceGroupID | None:
        """The id of the group a preset is bound to; the preset row records only its
        name, and what the preset belongs to is named by id."""
        if name is None:
            return None
        lookup = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(name))
        )
        return lookup.resolved_entity_id

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
            SearchResourcePresetsV2Action(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=ResourcePresetSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        return AdminSearchResourcePresetsPayload(
            items=[self._data_to_node(p) for p in result.items],
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

    async def batch_load_by_ids(
        self, ids: Sequence[ResourcePresetID]
    ) -> list[ResourcePresetNode | Exception | None]:
        """Batch load resource presets by id for DataLoader use, one answer per id."""
        if not ids:
            return []
        result = await self._resource_preset.bulk_get.run(BulkGetResourcePresetsAction(ids=ids))
        return [
            self._data_to_node(item.value)
            if item.value is not None
            else self.batch_load_failure(item.error)
            for item in result.items
        ]

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
            resource_group_id=await self._resource_group_id(resource_group_name),
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
        result = await self._resource_preset.update_preset.run(
            UpdateResourcePresetAction(updater=self._to_updater(input))
        )
        preset = result.resource_preset
        if not isinstance(input.resource_group_name, Unset):
            preset = await self.apply_resource_group(
                ResourcePresetID(input.id), input.resource_group_name
            )
        return UpdateResourcePresetPayload(
            resource_preset=self._data_to_node(preset),
        )

    async def apply_resource_group(
        self, preset_id: ResourcePresetID, resource_group_name: str | None
    ) -> ResourcePresetData:
        """Bind the preset to a resource group or to none, as its own run: that changes
        who is offered the preset, which a retune does not."""
        result = await self._resource_preset.set_preset_resource_group.run(
            SetResourcePresetResourceGroupAction(
                preset_id=preset_id, resource_group_name=resource_group_name
            )
        )
        return result.resource_preset

    async def purge(self, preset_id: UUID) -> DeleteResourcePresetPayload:
        """Permanently delete a resource preset by ID."""
        result = await self._resource_preset.delete_preset.run(
            DeleteResourcePresetAction(preset_id=ResourcePresetID(preset_id))
        )
        return DeleteResourcePresetPayload(id=result.resource_preset.id)

    async def partial_bulk_update(
        self, input: PartialBulkUpdateResourcePresetsInput
    ) -> PartialBulkPayload[ResourcePresetNode]:
        """Update several resource presets, answering for each one."""
        updaters = [self._to_updater(item) for item in input.items]
        for updater in updaters:
            if resource_slots := updater.resource_slots.optional_value():
                if not resource_slots.has_intrinsic_slots():
                    raise InvalidAPIParameters(
                        "ResourceSlot must have all intrinsic resource slots."
                    )
        result = await self._resource_preset.partial_bulk_update.run(
            PartialBulkUpdateResourcePresetsAction(updaters=updaters)
        )
        return self._to_partial_bulk_payload(result)

    async def partial_bulk_purge(
        self, input: PartialBulkPurgeResourcePresetsInput
    ) -> PartialBulkPayload[ResourcePresetNode]:
        """Permanently delete several resource presets, answering for each one."""
        result = await self._resource_preset.partial_bulk_purge.run(
            PartialBulkPurgeResourcePresetsAction(
                ids=[ResourcePresetID(preset_id) for preset_id in input.ids]
            )
        )
        return self._to_partial_bulk_payload(result)

    def _to_updater(
        self, input: UpdateResourcePresetInput | PartialBulkUpdateResourcePresetItemInput
    ) -> ResourcePresetUpdater:
        return ResourcePresetUpdater(
            preset_id=ResourcePresetID(input.id),
            resource_slots=OptionalState.from_unset(input.resource_slots).map(
                _resource_slot_entries_to_slot
            ),
            name=OptionalState.from_unset(input.name),
            shared_memory=TriState.from_unset(input.shared_memory).map(
                lambda v: BinarySize(v.bytes)
            ),
        )

    def _to_partial_bulk_payload(
        self, result: PartialBulkResult[ResourcePresetData]
    ) -> PartialBulkPayload[ResourcePresetNode]:
        return PartialBulkPayload[ResourcePresetNode](
            successes=[
                self._data_to_node(item.value) for item in result.items if item.value is not None
            ],
            failed=[
                PartialBulkFailure(id=item.entity_id, message=str(item.error))
                for item in result.items
                if item.error is not None
            ],
        )

    def _convert_filter(self, filter_: ResourcePresetFilter) -> list[QueryCondition]:
        """Convert ResourcePresetFilter DTO to QueryConditions."""
        fields = ResourcePresetSearchableFields.own
        conditions: list[QueryCondition] = [
            *self.apply_string_filter(filter_.name, fields.name.filter),
            *self.apply_string_filter(
                filter_.resource_group_name, fields.resource_group_name.filter
            ),
            *self.apply_uuid_filter(filter_.entity_id, fields.id.filter),
        ]
        if filter_.AND:
            for sub in filter_.AND:
                conditions.extend(self._convert_filter(sub))
        if filter_.OR:
            or_conds: list[QueryCondition] = []
            for sub in filter_.OR:
                sub_conditions = self._convert_filter(sub)
                if sub_conditions:
                    or_conds.append(combine_conditions_and(sub_conditions))
            if or_conds:
                conditions.append(combine_conditions_or(or_conds))
        if filter_.NOT:
            for sub in filter_.NOT:
                sub_conditions = self._convert_filter(sub)
                if sub_conditions:
                    conditions.append(negate_conditions(sub_conditions))
        return conditions

    def _convert_orders(self, orders: list[ResourcePresetOrder]) -> list[Any]:
        """Convert ResourcePresetOrder DTOs to QueryOrders."""
        fields = ResourcePresetSearchableFields.own
        result = []
        for order in orders:
            ascending = order.direction == ResourcePresetOrderDirection.ASC
            match order.field:
                case ResourcePresetOrderField.NAME:
                    result.append(fields.name.order.apply(ascending))
        return result

    @staticmethod
    def _data_to_node(data: ResourcePresetData) -> ResourcePresetNode:
        """Convert ResourcePresetData to ResourcePresetNode DTO."""
        return ResourcePresetNode(
            id=data.id,
            entity_id=data.entity_id(),
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
