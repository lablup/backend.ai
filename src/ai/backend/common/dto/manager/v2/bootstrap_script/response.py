from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID


class BootstrapScriptRevisionNode(BaseResponseModel):
    id: UUID
    field_id: UUID = Field(description="ID of the revision.")
    script_id: BootstrapScriptID = Field(description="ID of the script.")
    revision_number: int = Field(description="Number of the revision, counted from 1.")
    script: str = Field(description="Content of the script.")
    creator_id: UUID | None = Field(description="ID of the user who wrote the revision.")
    created_at: datetime = Field(description="Creation timestamp.")


class BootstrapScriptNode(BaseResponseModel):
    id: BootstrapScriptID
    field_id: BootstrapScriptID = Field(description="ID of the script.")
    user_id: UUID = Field(description="ID of the user the script is set on.")
    created_at: datetime = Field(description="Creation timestamp.")


class GetBootstrapScriptPayload(BaseResponseModel):
    bootstrap_script: BootstrapScriptNode = Field(description="The script.")


class CreateBootstrapScriptPayload(BaseResponseModel):
    revision: BootstrapScriptRevisionNode = Field(description="The first revision.")


class AddBootstrapScriptRevisionPayload(BaseResponseModel):
    revision: BootstrapScriptRevisionNode = Field(description="The added revision.")


class SwitchDefaultBootstrapScriptPayload(BaseResponseModel):
    bootstrap_script: BootstrapScriptNode = Field(description="The script that is the default.")


class PurgeBootstrapScriptPayload(BaseResponseModel):
    field_id: BootstrapScriptID = Field(description="ID of the purged script.")


class SearchBootstrapScriptsPayload(BaseResponseModel):
    """Payload for paginated bootstrap script search results."""

    items: list[BootstrapScriptNode] = Field(description="List of bootstrap script nodes.")
    total_count: int = Field(description="Total number of scripts matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
