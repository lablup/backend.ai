"""
Common types for resource slot DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "AgentResourceOrderField",
    "NumberFormatInfo",
    "OrderDirection",
    "ResourceAllocationOrderField",
    "ResourceOptsEntryDTO",
    "ResourceOptsEntryInfoDTO",
    "ResourceOptsDTOInput",
    "ResourceOptsInfoDTO",
    "ResourceSlotTypeOrderField",
)


class ResourceSlotTypeOrderField(StrEnum):
    """Fields available for ordering resource slot types."""

    SLOT_NAME = "slot_name"
    RANK = "rank"
    DISPLAY_NAME = "display_name"


class AgentResourceOrderField(StrEnum):
    """Fields available for ordering agent resource slots."""

    AGENT_ID = "agent_id"
    SLOT_NAME = "slot_name"
    CAPACITY = "capacity"
    USED = "used"


class ResourceAllocationOrderField(StrEnum):
    """Fields available for ordering resource allocations."""

    KERNEL_ID = "kernel_id"
    SLOT_NAME = "slot_name"
    REQUESTED = "requested"
    USED = "used"


class NumberFormatInfo(BaseResponseModel):
    """Number format configuration for a resource slot type."""

    binary: bool
    round_length: int


class ResourceOptsEntryDTO(BaseRequestModel):
    """Single resource option entry input with name and value."""

    name: str = Field(description="The name of this resource option (e.g., 'shmem').")
    value: str = Field(description="The value for this resource option (e.g., '64m').")


class ResourceOptsDTOInput(BaseRequestModel):
    """Resource options input containing multiple key-value entries."""

    entries: list[ResourceOptsEntryDTO] = Field(description="List of resource option entries.")


class ResourceOptsEntryInfoDTO(BaseResponseModel):
    """Single resource option entry with name and value."""

    name: str = Field(description="The name of this resource option (e.g., 'shmem').")
    value: str = Field(description="The value for this resource option (e.g., '64m').")


class ResourceOptsInfoDTO(BaseResponseModel):
    """Resource options containing multiple key-value entries."""

    entries: list[ResourceOptsEntryInfoDTO] = Field(description="List of resource option entries.")
