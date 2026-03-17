"""
Common types for Service Catalog DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.types import ServiceCatalogStatus

__all__ = (
    "EndpointInfo",
    "OrderDirection",
    "ServiceCatalogOrderField",
    "ServiceCatalogStatus",
    "ServiceCatalogStatusFilter",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ServiceCatalogOrderField(StrEnum):
    """Fields available for ordering service catalog entries."""

    SERVICE_GROUP = "service_group"
    DISPLAY_NAME = "display_name"
    REGISTERED_AT = "registered_at"
    LAST_HEARTBEAT = "last_heartbeat"
    STATUS = "status"


class ServiceCatalogStatusFilter(BaseRequestModel):
    """Filter for ServiceCatalogStatus enum field."""

    equals: ServiceCatalogStatus | None = None
    in_: list[ServiceCatalogStatus] | None = None
    not_equals: ServiceCatalogStatus | None = None
    not_in: list[ServiceCatalogStatus] | None = None


class EndpointInfo(BaseResponseModel):
    """Endpoint information embedded in ServiceCatalogNode."""

    id: UUID
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, Any] | None
