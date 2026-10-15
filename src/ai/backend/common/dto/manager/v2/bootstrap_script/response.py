"""Response DTOs for bootstrap script v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.user import UserID

__all__ = (
    "BootstrapScriptNode",
    "CreateBootstrapScriptPayload",
    "PurgeBootstrapScriptPayload",
    "SearchBootstrapScriptsPayload",
    "SwitchDefaultBootstrapScriptPayload",
    "UpdateBootstrapScriptPayload",
)


class BootstrapScriptNode(BaseResponseModel):
    """A script a user's sessions may run at startup."""

    id: BootstrapScriptID = Field(description="Bootstrap script id.")
    field_id: UUID = Field(description="UUID of the bootstrap script.")
    user_id: UserID = Field(description="Id of the user the script is set on.")
    script: str = Field(description="Script text.")
    is_default: bool = Field(description="Whether sessions of the user run this script.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last modification timestamp.")


class CreateBootstrapScriptPayload(BaseResponseModel):
    """Payload for bootstrap script creation."""

    bootstrap_script: BootstrapScriptNode = Field(description="Created bootstrap script.")


class UpdateBootstrapScriptPayload(BaseResponseModel):
    """Payload for bootstrap script update."""

    bootstrap_script: BootstrapScriptNode = Field(description="Updated bootstrap script.")


class SwitchDefaultBootstrapScriptPayload(BaseResponseModel):
    """Payload for switching the default bootstrap script."""

    bootstrap_script: BootstrapScriptNode = Field(description="The new default bootstrap script.")


class PurgeBootstrapScriptPayload(BaseResponseModel):
    """Payload for bootstrap script purge."""

    id: BootstrapScriptID = Field(description="Id of the purged bootstrap script.")


class SearchBootstrapScriptsPayload(BaseResponseModel):
    """Payload for paginated bootstrap script search results."""

    items: list[BootstrapScriptNode] = Field(description="Bootstrap script nodes.")
    total_count: int = Field(description="Total count of the user's bootstrap scripts.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
