"""Entity type and id of the images table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("ImageEntityType", "ImageID")


class ImageEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "image"

    @override
    @classmethod
    def description(cls) -> str:
        return "A container image in a registry, one row per architecture."


class ImageID(EntityIdentifier):
    """An image's entity id."""

    @override
    def entity_type(self) -> EntityType:
        return ImageEntityType()
