from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.repositories.resource_slot.updaters import ResourceSlotTypeUpdater


@dataclass
class UpdateResourceSlotTypeAction(
    UpdateGlobalOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]
):
    """Update the display and scheduling flags of one resource slot type.

    ``slot_name`` and ``slot_type`` are not updatable — see
    :class:`~ai.backend.manager.repositories.resource_slot.updaters.ResourceSlotTypeUpdater`.
    """

    updater: ResourceSlotTypeUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_resource_slot_type"

    @override
    def to_updater(self) -> ResourceSlotTypeUpdater:
        return self.updater
