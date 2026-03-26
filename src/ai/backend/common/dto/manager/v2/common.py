"""Shared types used across all v2 DTO domains."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "OrderDirection",
    "ResourceSlotEntryInput",
)


class OrderDirection(StrEnum):
    """Order direction for sorting. Shared across all v2 DTO domains."""

    ASC = "ASC"
    DESC = "DESC"


class ResourceSlotEntryInput(BaseRequestModel):
    """Single resource slot entry with resource type and quantity.

    Shared across all domains that accept resource allocations (session, deployment, etc.).
    """

    resource_type: str = Field(description="Resource type identifier (e.g., 'cpu', 'mem').")
    quantity: str = Field(description="Quantity of the resource as a decimal string.")
