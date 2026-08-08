from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.repositories.resource_slot.purgers import ResourceSlotTypePurger


@dataclass
class PurgeResourceSlotTypeAction(PurgeGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Remove a resource slot type, refusing while anything still references it."""

    purger: ResourceSlotTypePurger

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_resource_slot_type"

    @override
    def to_purger(self) -> ResourceSlotTypePurger:
        return self.purger
