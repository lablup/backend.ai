from ai.backend.common.data.entity.types import EntityType

__all__ = ("RUNTIME_VARIANT_PRESET_ENTITY_TYPE",)


# The presets of a runtime variant are their own catalog: the actions name this rather
# than the variant's type so audit rows and permission lookups do not conflate the two.
RUNTIME_VARIANT_PRESET_ENTITY_TYPE = EntityType("runtime_variant_preset")
