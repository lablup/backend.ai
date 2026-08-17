from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "SERVICE_CATALOG_ENTITY_TYPE",
    "ServiceCatalogID",
)


# Raw string mirroring the RBAC-managed EntityType.SERVICE_CATALOG value.
SERVICE_CATALOG_ENTITY_TYPE = EntityType("service_catalog")


class ServiceCatalogID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SERVICE_CATALOG_ENTITY_TYPE
