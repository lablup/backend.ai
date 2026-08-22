from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "DEPLOYMENT_PRESET_ENTITY_TYPE",
    "DeploymentPresetID",
)


DEPLOYMENT_PRESET_ENTITY_TYPE = EntityType("deployment_preset")


class DeploymentPresetID(EntityIdentifier):
    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE
