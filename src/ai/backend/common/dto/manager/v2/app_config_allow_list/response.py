"""Response DTOs for app_config_allow_list v2."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.app_config.types import AppConfigPermission, AppConfigScopeType

__all__ = (
    "AppConfigAllowListNode",
    "CreateAppConfigAllowListPayload",
    "PurgeAppConfigAllowListPayload",
    "SearchAppConfigAllowListPayload",
    "UpdateAppConfigAllowListPayload",
)


class AppConfigAllowListNode(BaseResponseModel):
    """Node model representing an app config allow-list entry."""

    id: UUID = Field(description="App config allow-list entry UUID.")
    config_name: str = Field(description="Gated config name.")
    scope_type: AppConfigScopeType = Field(description="Scope type the entry permits writes at.")
    rank: int = Field(
        description=("Merge rank applied to fragments under this entry (low to high; higher wins).")
    )
    permission: AppConfigPermission = Field(
        description="Write policy for the fragments under this entry (rw = scope owner may write, ro = superadmin only)."
    )
    created_at: datetime = Field(description="Creation timestamp (UTC).")
    updated_at: datetime = Field(description="Last update timestamp (UTC).")


class CreateAppConfigAllowListPayload(BaseResponseModel):
    """Payload for app config allow-list entry creation."""

    app_config_allow_list: AppConfigAllowListNode = Field(
        description="Created app config allow-list entry."
    )


class UpdateAppConfigAllowListPayload(BaseResponseModel):
    """Payload for app config allow-list entry update."""

    app_config_allow_list: AppConfigAllowListNode = Field(
        description="Updated app config allow-list entry."
    )


class PurgeAppConfigAllowListPayload(BaseResponseModel):
    """Payload for app config allow-list entry purge."""

    id: UUID = Field(description="UUID of the purged app config allow-list entry.")


class SearchAppConfigAllowListPayload(BaseResponseModel):
    """Payload for paginated app config allow-list search results."""

    items: list[AppConfigAllowListNode] = Field(description="App config allow-list nodes.")
    total_count: int = Field(description="Total count matching the query.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
