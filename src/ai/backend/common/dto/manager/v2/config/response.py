"""
Response DTOs for config DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "BootstrapScriptNode",
    "CreateDotfilePayload",
    "DeleteDotfilePayload",
    "DotfileListPayload",
    "DotfileNode",
    "UpdateBootstrapScriptPayload",
    "UpdateDotfilePayload",
)


class DotfileNode(BaseResponseModel):
    """Node model representing a dotfile entity."""

    path: str = Field(description="Dotfile path")
    permission: str = Field(description="Unix file permission in octal notation")
    data: str = Field(description="Dotfile content")


class CreateDotfilePayload(BaseResponseModel):
    """Payload for dotfile creation mutation result."""


class UpdateDotfilePayload(BaseResponseModel):
    """Payload for dotfile update mutation result."""


class DeleteDotfilePayload(BaseResponseModel):
    """Payload for dotfile deletion mutation result."""

    success: bool = Field(description="Whether the deletion was successful")


class DotfileListPayload(BaseResponseModel):
    """Payload for dotfile listing."""

    items: list[DotfileNode] = Field(description="List of dotfile entries")


class BootstrapScriptNode(BaseResponseModel):
    """Node model representing the bootstrap script."""

    script: str = Field(description="Bootstrap script content")


class UpdateBootstrapScriptPayload(BaseResponseModel):
    """Payload for bootstrap script update mutation result."""
