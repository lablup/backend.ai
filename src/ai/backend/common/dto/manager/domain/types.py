"""
Common types for domain DTOs.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "DomainOrder",
    "DomainOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class DomainOrderField(StrEnum):
    """Fields available for ordering domains."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


class DomainOrder(BaseRequestModel):
    """Order specification for domains."""

    field: DomainOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")
