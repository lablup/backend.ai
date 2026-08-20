"""Entity type and id of the images table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("IMAGE_ENTITY_TYPE", "ImageID")

IMAGE_ENTITY_TYPE = EntityType("image")


class ImageID(EntityIdentifier):
    """An image's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return IMAGE_ENTITY_TYPE
