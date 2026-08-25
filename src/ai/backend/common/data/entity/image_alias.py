"""Field type and id of the image_aliases table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("IMAGE_ALIAS_FIELD_TYPE", "ImageAliasID")

IMAGE_ALIAS_FIELD_TYPE = FieldType("image_alias")


class ImageAliasID(FieldIdentifier):
    """An image alias row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return IMAGE_ALIAS_FIELD_TYPE
