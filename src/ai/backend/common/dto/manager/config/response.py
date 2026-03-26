"""
Response DTOs for config (dotfile) system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel, BaseRootResponseModel

__all__ = (
    "DotfileItem",
    "DotfileListItem",
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


class DotfileListItem(BaseModel):
    """A dotfile entry for list responses (backward compatible field names)."""

    path: str = Field(description="Dotfile path")
    permission: str = Field(description="Unix file permission in octal notation")
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


class ListDotfilesResponse(BaseRootResponseModel[list[DotfileListItem]]):
    """Response for listing dotfiles (plain array for backward compatibility)."""


class GetBootstrapScriptResponse(BaseRootResponseModel[str]):
    """Response for retrieving the bootstrap script (plain string for backward compatibility)."""


class UpdateBootstrapScriptResponse(BaseResponseModel):
    """Response for bootstrap script update (empty body)."""
