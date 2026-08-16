from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RUNTIME_VARIANT_ENTITY_TYPE",
    "RuntimeVariantID",
)


# Raw string mirroring the RBAC-managed EntityType.RUNTIME_VARIANT value.
RUNTIME_VARIANT_ENTITY_TYPE = EntityType("runtime_variant")


class RuntimeVariantID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE
