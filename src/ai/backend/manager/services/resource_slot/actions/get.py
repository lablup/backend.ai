from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.queriers import ResourceSlotTypeQuerier
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow


@dataclass(frozen=True)
class GetResourceSlotTypeAction(
    GetSingleEntityOpsAction[ResourceSlotTypeRow, ResourceSlotTypeData]
):
    """Read one slot type by its id."""

    slot_type_id: ResourceSlotTypeUUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.slot_type_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_slot_type"

    @override
    def to_querier(self) -> ResourceSlotTypeQuerier:
        return ResourceSlotTypeQuerier(uuid=self.slot_type_id)
