from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("PresetResourceSlotID",)


DEPLOYMENT_PRESET_RESOURCE_SLOT_FIELD_TYPE = FieldType("deployment_preset_resource_slot")


class PresetResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment preset declares."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DEPLOYMENT_PRESET_RESOURCE_SLOT_FIELD_TYPE
