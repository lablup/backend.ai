"""
Shared types for Prometheus Query Definition DTOs.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "OrderDirection",
    "QueryDefinitionOrder",
    "QueryDefinitionOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class QueryDefinitionOrderField(StrEnum):
    """Fields available for ordering prometheus query definitions."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class QueryDefinitionOrder(BaseRequestModel):
    """Order specification for prometheus query definitions."""

    field: QueryDefinitionOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")
