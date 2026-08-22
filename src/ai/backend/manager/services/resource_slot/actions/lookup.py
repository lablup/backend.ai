from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_slot import (
    RESOURCE_SLOT_TYPE_ENTITY_TYPE,
    ResourceSlotTypeUUID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.resource_slot.lookups import ResourceSlotTypeLookup
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow


@dataclass(frozen=True)
class ResourceSlotTypeNameKey(LookupKey):
    """The slot name a caller passes instead of the type's row."""

    slot_name: str

    @override
    def kind(self) -> str:
        return "resource_slot_type_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"slot_name": self.slot_name}


@dataclass
class LookupResourceSlotTypeAction(
    LookupEntityOpsAction[ResourceSlotTypeRow, ResourceSlotTypeUUID]
):
    """Resolve a slot name into the type it names."""

    slot_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_resource_slot_type"

    @override
    def lookup_key(self) -> ResourceSlotTypeNameKey:
        return ResourceSlotTypeNameKey(slot_name=self.slot_name)

    @override
    def to_lookup(self) -> ResourceSlotTypeLookup:
        return ResourceSlotTypeLookup(slot_name=self.slot_name)
