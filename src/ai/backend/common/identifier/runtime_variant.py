from typing import override

from ai.backend.common.data.entity.runtime_variant import RUNTIME_VARIANT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("RuntimeVariantID",)


class RuntimeVariantID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE
