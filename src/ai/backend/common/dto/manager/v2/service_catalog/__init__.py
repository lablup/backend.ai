"""
Service Catalog DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
    CreateServiceCatalogInput,
    DeleteServiceCatalogInput,
    EndpointInput,
    HeartbeatInput,
    ServiceCatalogFilter,
    ServiceCatalogOrder,
    UpdateServiceCatalogInput,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import (
    AdminSearchServiceCatalogsPayload,
    CreateServiceCatalogPayload,
    DeleteServiceCatalogPayload,
    HeartbeatPayload,
    ServiceCatalogNode,
    UpdateServiceCatalogPayload,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
    OrderDirection,
    ServiceCatalogOrderField,
    ServiceCatalogStatus,
    ServiceCatalogStatusFilter,
)

__all__ = (
    # Types
    "EndpointInfo",
    "OrderDirection",
    "ServiceCatalogOrderField",
    "ServiceCatalogStatus",
    "ServiceCatalogStatusFilter",
    # Input models (request)
    "AdminSearchServiceCatalogsInput",
    "CreateServiceCatalogInput",
    "DeleteServiceCatalogInput",
    "EndpointInput",
    "HeartbeatInput",
    "ServiceCatalogFilter",
    "ServiceCatalogOrder",
    "UpdateServiceCatalogInput",
    # Node and Payload models (response)
    "AdminSearchServiceCatalogsPayload",
    "CreateServiceCatalogPayload",
    "DeleteServiceCatalogPayload",
    "HeartbeatPayload",
    "ServiceCatalogNode",
    "UpdateServiceCatalogPayload",
)
