from typing import override

from ai.backend.common.data.entity.deployment_preset import DEPLOYMENT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType

__all__ = ("PresetResourceSlotID",)


DEPLOYMENT_PRESET_RESOURCE_SLOT_FIELD_TYPE = FieldType("deployment_preset_resource_slot")


class PresetResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment preset declares."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_PRESET_RESOURCE_SLOT_FIELD_TYPE

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE
