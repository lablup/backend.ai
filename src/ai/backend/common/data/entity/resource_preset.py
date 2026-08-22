"""Entity type and id of the resource presets table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("RESOURCE_PRESET_ENTITY_TYPE", "ResourcePresetID")

RESOURCE_PRESET_ENTITY_TYPE = EntityType("resource_preset")


class ResourcePresetID(EntityIdentifier):
    """A resource preset's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return RESOURCE_PRESET_ENTITY_TYPE
