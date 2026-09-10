from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RuntimeVariantPresetEntityType",
    "RuntimeVariantPresetID",
)


# The presets of a runtime variant are their own catalog: the actions name this rather
# than the variant's type so audit rows and permission lookups do not conflate the two.
class RuntimeVariantPresetEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "runtime_variant_preset"

    @override
    @classmethod
    def description(cls) -> str:
        return "A saved setting of a runtime variant."


class RuntimeVariantPresetID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return RuntimeVariantPresetEntityType()
