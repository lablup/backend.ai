"""
Common types for Model Serving DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import RuntimeVariant

__all__ = (
    "EndpointLifecycle",
    "OrderDirection",
    "RouteInfoSummary",
    "RuntimeVariant",
    "ServiceOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ServiceOrderField(StrEnum):
    """Fields available for ordering model serving services."""

    NAME = "name"
    CREATED_AT = "created_at"


class RouteInfoSummary(BaseResponseModel):
    """Compact route view embedded in ServiceNode."""

    route_id: UUID
    session_id: UUID | None
    traffic_ratio: float
