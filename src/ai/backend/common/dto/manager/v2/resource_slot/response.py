"""
Response DTOs for resource slot DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import NumberFormatInfo

__all__ = ("ResourceSlotTypeNode",)


class ResourceSlotTypeNode(BaseResponseModel):
    """Node model representing a resource slot type entity."""

    slot_name: str = Field(
        description="Unique identifier for the resource slot (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    slot_type: str = Field(
        description="Category of the slot type (e.g., 'count', 'bytes', 'unique-count')."
    )
    display_name: str = Field(description="Human-readable name for display in UIs.")
    description: str = Field(
        description="Longer description of what this resource slot represents."
    )
    display_unit: str = Field(
        description="Unit label used when displaying resource amounts (e.g., 'GiB', 'cores')."
    )
    display_icon: str = Field(
        description="Icon identifier for UI rendering (e.g., 'cpu', 'memory', 'gpu')."
    )
    number_format: NumberFormatInfo = Field(
        description="Number formatting rules (binary vs decimal prefix, rounding)."
    )
    rank: int = Field(description="Display ordering rank. Lower values appear first.")
