from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ObjectStorageEntityType",
    "ObjectStorageID",
)


class ObjectStorageEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "object_storage"

    @override
    @classmethod
    def description(cls) -> str:
        return "An object storage backend behind a storage namespace."


class ObjectStorageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ObjectStorageEntityType()
