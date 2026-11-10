from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("PresetResourceSlotID",)


class DeploymentPresetResourceSlotFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_preset_resource_slot"

    @override
    @classmethod
    def description(cls) -> str:
        return "One slot's amount a deployment preset declares."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentPresetEntityType


class PresetResourceSlotID(FieldIdentifier):
    """One slot's amount a deployment preset declares."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DeploymentPresetResourceSlotFieldType()
