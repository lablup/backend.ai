from typing import override

from ai.backend.common.data.entity.storage_namespace import STORAGE_NAMESPACE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("StorageNamespaceID",)


class StorageNamespaceID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE
