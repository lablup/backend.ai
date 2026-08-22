from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.deployment_preset import (
    DEPLOYMENT_PRESET_ENTITY_TYPE,
    DeploymentPresetID,
)
from ai.backend.common.data.entity.preset_resource_slot import PresetResourceSlotID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.deployment_revision_preset.lookups import (
    PresetResourceSlotOwnerLookup,
)


@dataclass(frozen=True)
class PresetResourceSlotIDLookupKey(LookupKey):
    """A slot row's id, resolved into the preset that owns it."""

    slot_id: PresetResourceSlotID

    @override
    def kind(self) -> str:
        return "preset_resource_slot_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.slot_id)}


@dataclass
class LookupPresetResourceSlotOwnerAction(
    LookupFieldOwnerOpsAction[PresetResourceSlotID, DeploymentPresetID]
):
    """The preset a slot row belongs to."""

    slot_id: PresetResourceSlotID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_preset_resource_slot_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return PresetResourceSlotIDLookupKey(self.slot_id)

    @override
    def field_id(self) -> PresetResourceSlotID:
        return self.slot_id

    @override
    def to_owner_lookup(self) -> PresetResourceSlotOwnerLookup:
        return PresetResourceSlotOwnerLookup()


@dataclass
class LookupBulkPresetResourceSlotOwnerAction(
    LookupBulkFieldOwnerOpsAction[PresetResourceSlotID, DeploymentPresetID]
):
    """The presets several slot rows belong to."""

    slot_ids: Sequence[PresetResourceSlotID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_preset_resource_slot_owner"

    @override
    def to_lookup_key(self, field_id: PresetResourceSlotID) -> LookupKey:
        return PresetResourceSlotIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[PresetResourceSlotID]:
        return tuple(self.slot_ids)

    @override
    def to_owner_lookup(self) -> PresetResourceSlotOwnerLookup:
        return PresetResourceSlotOwnerLookup()
