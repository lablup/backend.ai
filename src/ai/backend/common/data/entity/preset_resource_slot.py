from typing import override

from ai.backend.common.data.entity.deployment_preset import DEPLOYMENT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("PresetResourceSlotID",)


class PresetResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment preset declares."""

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE
