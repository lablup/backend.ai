from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "DeploymentPresetEntityType",
    "DeploymentPresetID",
)


class DeploymentPresetEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_preset"

    @override
    @classmethod
    def description(cls) -> str:
        return "A reusable revision setting a deployment can start from."


class DeploymentPresetID(EntityIdentifier):
    @classmethod
    @override
    def entity_type(cls) -> EntityType:
        return DeploymentPresetEntityType()
