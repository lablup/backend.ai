"""
Common types for Service Catalog DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.types import ServiceCatalogStatus

__all__ = (
    "OrderDirection",
    "ServiceCatalogOrderField",
    "ServiceCatalogStatus",
    "ServiceCatalogStatusFilter",
)


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
