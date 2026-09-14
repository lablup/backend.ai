"""Field type and id of the image_aliases table."""

from typing import override

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("ImageAliasFieldType", "ImageAliasID")


class ImageAliasFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "image_alias"

    @override
    @classmethod
    def description(cls) -> str:
        return "An alternate name of an image."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return ImageEntityType


class ImageAliasID(FieldIdentifier):
    """An image alias row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ImageAliasFieldType()
