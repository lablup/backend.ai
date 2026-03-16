"""
Common types for infra DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AcceleratorMetadataInfo",
    "InfraOrderField",
    "NumberFormatInfo",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class InfraOrderField(StrEnum):
    """Fields available for ordering infrastructure resources."""

    NAME = "name"


class NumberFormatInfo(BaseResponseModel):
    """Number formatting configuration for resource slot display."""

    binary: bool = Field(description="Whether to use binary (base-2) formatting.")
    round_length: int = Field(description="Number of decimal places to round to.")


class AcceleratorMetadataInfo(BaseResponseModel):
    """Metadata for an accelerator resource slot."""

    slot_name: str = Field(description="Internal slot name identifier.")
    description: str = Field(description="Human-readable description of the accelerator.")
    human_readable_name: str = Field(description="Short display name for the accelerator.")
    display_unit: str = Field(description="Unit label for display (e.g., 'Core', 'GiB', 'GPU').")
    number_format: NumberFormatInfo = Field(description="Number formatting configuration.")
    display_icon: str = Field(description="Icon identifier for UI rendering.")
