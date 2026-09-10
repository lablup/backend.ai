from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ServiceCatalogEntityType",
    "ServiceCatalogID",
)


class ServiceCatalogEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "service_catalog"

    @override
    @classmethod
    def description(cls) -> str:
        return "One running component that announced itself to the manager."


class ServiceCatalogID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ServiceCatalogEntityType()
