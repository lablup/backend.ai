"""
Common types for resource slot DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AgentResourceOrderField",
    "NumberFormatInfo",
    "OrderDirection",
    "ResourceAllocationOrderField",
    "ResourceSlotTypeOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ResourceSlotTypeOrderField(StrEnum):
    """Fields available for ordering resource slot types."""

    SLOT_NAME = "slot_name"
    RANK = "rank"
    DISPLAY_NAME = "display_name"


class AgentResourceOrderField(StrEnum):
    """Fields available for ordering agent resource slots."""

    AGENT_ID = "agent_id"
    SLOT_NAME = "slot_name"


class ResourceAllocationOrderField(StrEnum):
    """Fields available for ordering resource allocations."""

    KERNEL_ID = "kernel_id"
    SLOT_NAME = "slot_name"


class NumberFormatInfo(BaseResponseModel):
    """Number format configuration for a resource slot type."""

    binary: bool
    round_length: int
