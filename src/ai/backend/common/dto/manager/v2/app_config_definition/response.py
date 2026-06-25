"""Response DTOs for app_config_definition v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AppConfigDefinitionNode",
    "CreateAppConfigDefinitionPayload",
    "PurgeAppConfigDefinitionPayload",
    "SearchAppConfigDefinitionsPayload",
)


class AppConfigDefinitionNode(BaseResponseModel):
    """Node model representing a registered app config definition."""

    id: UUID = Field(description="App config definition UUID.")
    config_name: str = Field(description="Registered config name.")
    created_at: datetime = Field(description="Creation timestamp (UTC).")
    updated_at: datetime = Field(description="Last update timestamp (UTC).")


class CreateAppConfigDefinitionPayload(BaseResponseModel):
    """Payload for app config definition creation."""

    app_config_definition: AppConfigDefinitionNode = Field(
        description="Created app config definition."
    )


class PurgeAppConfigDefinitionPayload(BaseResponseModel):
    """Payload for app config definition purge."""

    id: UUID = Field(description="UUID of the purged app config definition.")


class SearchAppConfigDefinitionsPayload(BaseResponseModel):
    """Payload for paginated app config definition search results."""

    items: list[AppConfigDefinitionNode] = Field(description="App config definition nodes.")
    total_count: int = Field(description="Total count matching the query.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
