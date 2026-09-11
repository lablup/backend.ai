from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RuntimeVariantEntityType",
    "RuntimeVariantID",
)


class RuntimeVariantEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "runtime_variant"

    @override
    @classmethod
    def description(cls) -> str:
        return "A model serving runtime a deployment revision runs on."


class RuntimeVariantID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return RuntimeVariantEntityType()
