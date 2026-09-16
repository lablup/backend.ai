from typing import override

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = (
    "ServiceCatalogEndpointFieldType",
    "ServiceCatalogEndpointID",
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


class ServiceCatalogEndpointFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "service_catalog_endpoint"

    @override
    @classmethod
    def description(cls) -> str:
        return "An address a registered service instance can be reached at."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return ServiceCatalogEntityType


class ServiceCatalogEndpointID(FieldIdentifier):
    """An endpoint's id; the service instance announcing it owns the row."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ServiceCatalogEndpointFieldType()
