"""Response DTOs for app_config_fragment v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.app_config.types import AppConfigScopeType

__all__ = (
    "AppConfigFragmentNode",
    "CreateAppConfigFragmentPayload",
    "PurgeAppConfigFragmentPayload",
    "SearchAppConfigFragmentPayload",
    "UpdateAppConfigFragmentPayload",
)


class AppConfigFragmentNode(BaseResponseModel):
    """Node model representing one app config fragment."""

    id: UUID = Field(description="App config fragment UUID.")
    config_name: str = Field(description="Config name the fragment belongs to.")
    scope_type: AppConfigScopeType = Field(description="Scope the fragment is written at.")
    scope_id: str = Field(description="Scope identifier (public / domain name / user id).")
    rank: int = Field(description="Merge rank (lower merges first, higher overrides).")
    config: dict[str, Any] = Field(description="The fragment's JSON config document.")
    created_at: datetime = Field(description="Creation timestamp (UTC).")
    updated_at: datetime = Field(description="Last update timestamp (UTC).")


class CreateAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment creation."""

    app_config_fragment: AppConfigFragmentNode = Field(description="Created app config fragment.")


class UpdateAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment update."""

    app_config_fragment: AppConfigFragmentNode = Field(description="Updated app config fragment.")


class PurgeAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment purge."""

    id: UUID = Field(description="UUID of the purged app config fragment.")


class SearchAppConfigFragmentPayload(BaseResponseModel):
    """Payload for paginated app config fragment search results."""

    items: list[AppConfigFragmentNode] = Field(description="App config fragment nodes.")
    total_count: int = Field(description="Total count matching the query.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
