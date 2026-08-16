from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import RUNTIME_VARIANT_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("RuntimeVariantPresetID",)


class RuntimeVariantPresetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE
