"""
Response DTOs for config (dotfile) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "DotfileItem",
    "CreateDotfileResponse",
    "UpdateDotfileResponse",
    "DeleteDotfileResponse",
    "GetDotfileResponse",
    "ListDotfilesResponse",
    "GetBootstrapScriptResponse",
    "UpdateBootstrapScriptResponse",
)


class DotfileItem(BaseModel):
    """A single dotfile entry."""

    path: str = Field(description="Dotfile path")
    perm: str = Field(description="Unix file permission in octal notation")
    data: str = Field(description="Dotfile content")


class CreateDotfileResponse(BaseResponseModel):
    """Response for dotfile creation (empty body)."""


class UpdateDotfileResponse(BaseResponseModel):
    """Response for dotfile update (empty body)."""


class DeleteDotfileResponse(BaseResponseModel):
    """Response for dotfile deletion."""

    success: bool = Field(description="Whether the deletion was successful")


class GetDotfileResponse(BaseResponseModel):
    """Response for retrieving a single dotfile."""

    path: str = Field(description="Dotfile path")
    perm: str = Field(description="Unix file permission in octal notation")
    data: str = Field(description="Dotfile content")


class ListDotfilesResponse(BaseResponseModel):
    """Response for listing dotfiles."""

    items: list[DotfileItem] = Field(description="List of dotfile entries")


class GetBootstrapScriptResponse(BaseResponseModel):
    """Response for retrieving the bootstrap script."""

    script: str = Field(description="Bootstrap script content")


class UpdateBootstrapScriptResponse(BaseResponseModel):
    """Response for bootstrap script update (empty body)."""
