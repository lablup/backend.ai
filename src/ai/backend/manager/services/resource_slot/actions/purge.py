from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.purgers import ResourceSlotTypePurger
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow


@dataclass
class PurgeResourceSlotTypeAction(PurgeEntityOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Remove a resource slot type, refusing while anything still references it."""

    purger: ResourceSlotTypePurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_resource_slot_type"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> ResourceSlotTypePurger:
        return self.purger
