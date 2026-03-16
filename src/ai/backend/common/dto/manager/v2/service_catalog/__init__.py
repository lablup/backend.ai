"""
Service Catalog DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.service_catalog.request import (
    CreateServiceCatalogInput,
    DeleteServiceCatalogInput,
    EndpointInput,
    HeartbeatInput,
    UpdateServiceCatalogInput,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import (
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
)

__all__ = (
    # Types
    "EndpointInfo",
    "OrderDirection",
    "ServiceCatalogOrderField",
    "ServiceCatalogStatus",
    # Input models (request)
    "CreateServiceCatalogInput",
    "DeleteServiceCatalogInput",
    "EndpointInput",
    "HeartbeatInput",
    "UpdateServiceCatalogInput",
    # Node and Payload models (response)
    "CreateServiceCatalogPayload",
    "DeleteServiceCatalogPayload",
    "HeartbeatPayload",
    "ServiceCatalogNode",
    "UpdateServiceCatalogPayload",
)
