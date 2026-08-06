from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.repositories.resource_slot.creators import ResourceSlotTypeCreator


@dataclass
class CreateResourceSlotTypeAction(
    CreateGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]
):
    """Register a new resource slot type in the catalog."""

    creator: ResourceSlotTypeCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE

    @override
    def to_creator(self) -> ResourceSlotTypeCreator:
        return self.creator
