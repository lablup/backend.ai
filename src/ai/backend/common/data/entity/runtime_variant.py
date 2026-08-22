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
    def entity_type(self) -> EntityType:
        return RUNTIME_VARIANT_ENTITY_TYPE
