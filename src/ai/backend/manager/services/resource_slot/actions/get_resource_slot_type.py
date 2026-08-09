from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.repositories.resource_slot.queriers import ResourceSlotTypeQuerier


@dataclass
class GetResourceSlotTypeAction(GetGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Read one resource slot type from the catalog; every authenticated user may."""

    slot_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_slot_type"

    @override
    def to_querier(self) -> ResourceSlotTypeQuerier:
        return ResourceSlotTypeQuerier(slot_name=self.slot_name)
