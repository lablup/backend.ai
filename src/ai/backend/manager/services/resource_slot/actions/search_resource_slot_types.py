from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.repositories.resource_slot.searchers import ResourceSlotTypeSearcher


@dataclass
class SearchResourceSlotTypesAction(
    SearchGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]
):
    """Page through the resource slot type catalog; every authenticated user may."""

    searcher: ResourceSlotTypeSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_resource_slot_types"

    @override
    def to_searcher(self) -> ResourceSlotTypeSearcher:
        return self.searcher
