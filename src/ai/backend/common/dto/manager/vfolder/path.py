"""
Path parameter DTOs for VFolder API endpoints.
"""

from __future__ import annotations

import uuid

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "VFolderForceDeletePath",
    "VFolderIDPath",
    "VFolderInvitationIDPath",
    "VFolderNamePath",
)


class VFolderIDPath(BaseRequestModel):
    """Path parameter for endpoints using vfolder ID."""

    vfolder_id: uuid.UUID = Field(validation_alias=AliasChoices("id", "vfolderId"))


class VFolderNamePath(BaseRequestModel):
    """Path parameter for endpoints using vfolder name."""

    name: str = Field(description="VFolder name or ID to resolve")


class VFolderInvitationIDPath(BaseRequestModel):
    """Path parameter for invitation endpoints."""

    inv_id: str = Field(description="Invitation ID")


class VFolderForceDeletePath(BaseRequestModel):
    """Path parameter for force delete endpoint."""

    folder_id: uuid.UUID = Field(description="VFolder ID to force delete")
