"""
Response DTOs for Resource Slot Type REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

__all__ = (
    "NumberFormatDTO",
    "ResourceSlotTypeDTO",
    "PaginationInfo",
    "SearchResourceSlotTypesResponse",
    "GetResourceSlotTypeResponse",
)


class NumberFormatDTO(BaseModel):
    """DTO for number format data."""

    binary: bool = Field(description="Whether to use binary (1024-based) units")
    round_length: int = Field(description="Number of decimal places to round to")


class ResourceSlotTypeDTO(BaseModel):
    """DTO for resource slot type data."""

    slot_name: str = Field(description="Unique slot name identifier")
    slot_type: str = Field(description="Slot type (e.g., count, bytes)")
    display_name: str = Field(description="Human-readable display name")
    description: str = Field(description="Description of the resource slot type")
    display_unit: str = Field(description="Unit string for display purposes")
    display_icon: str = Field(description="Icon identifier for display purposes")
    number_format: NumberFormatDTO = Field(description="Number formatting options")
    rank: int = Field(description="Display rank/order")


class SearchResourceSlotTypesResponse(BaseResponseModel):
    """Response for searching resource slot types."""

    items: list[ResourceSlotTypeDTO] = Field(description="List of resource slot types")
    pagination: PaginationInfo = Field(description="Pagination information")


class GetResourceSlotTypeResponse(BaseResponseModel):
    """Response for getting a single resource slot type."""

    item: ResourceSlotTypeDTO = Field(description="Resource slot type data")
