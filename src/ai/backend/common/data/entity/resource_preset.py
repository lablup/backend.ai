"""Entity type and id of the resource presets table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ResourcePresetEntityType", "ResourcePresetID")


class ResourcePresetEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "resource_preset"

    @override
    @classmethod
    def description(cls) -> str:
        return "A named set of resource amounts a session can request."


class ResourcePresetID(EntityIdentifier):
    """A resource preset's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return ResourcePresetEntityType()
