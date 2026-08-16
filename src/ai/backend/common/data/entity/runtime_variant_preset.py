from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RUNTIME_VARIANT_PRESET_ENTITY_TYPE",
    "RuntimeVariantPresetID",
)


# The presets of a runtime variant are their own catalog: the actions name this rather
# than the variant's type so audit rows and permission lookups do not conflate the two.
RUNTIME_VARIANT_PRESET_ENTITY_TYPE = EntityType("runtime_variant_preset")


class RuntimeVariantPresetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE
