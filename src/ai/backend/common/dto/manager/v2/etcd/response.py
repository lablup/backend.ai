"""
Response DTOs for etcd DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AcceleratorMetadataNode",
    "ConfigOkPayload",
    "ConfigValuePayload",
    "NumberFormatInfo",
    "ResourceMetadataPayload",
    "ResourceSlotNode",
    "VfolderTypesPayload",
)


class ResourceSlotNode(BaseResponseModel):
    """Node representing available resource slot types."""

    slots: dict[str, str] = Field(description="Mapping of slot name to slot type string.")


class NumberFormatInfo(BaseResponseModel):
    """Number formatting configuration for resource slot display."""

    binary: bool = Field(description="Whether to use binary (base-2) formatting.")
    round_length: int = Field(description="Number of decimal places to round to.")


class AcceleratorMetadataNode(BaseResponseModel):
    """Node representing metadata for an accelerator resource slot."""

    slot_name: str = Field(description="Internal slot name identifier.")
    description: str = Field(description="Human-readable description of the accelerator.")
    human_readable_name: str = Field(description="Short display name for the accelerator.")
    display_unit: str = Field(description="Unit label for display (e.g., 'Core', 'GiB', 'GPU').")
    number_format: NumberFormatInfo = Field(description="Number formatting configuration.")
    display_icon: str = Field(description="Icon identifier for UI rendering.")


class ResourceMetadataPayload(BaseResponseModel):
    """Payload containing metadata for accelerator resource slots."""

    metadata: dict[str, AcceleratorMetadataNode] = Field(
        description="Mapping of slot name to accelerator metadata."
    )


class VfolderTypesPayload(BaseResponseModel):
    """Payload containing available virtual folder types."""

    types: list[str] = Field(description="List of available vfolder type strings.")


class ConfigValuePayload(BaseResponseModel):
    """Payload for etcd config read result."""

    result: Any = Field(description="The value read from etcd.")


class ConfigOkPayload(BaseResponseModel):
    """Payload for etcd config write/delete confirmation."""

    result: str = Field(default="ok", description="Operation result, defaults to 'ok'.")
