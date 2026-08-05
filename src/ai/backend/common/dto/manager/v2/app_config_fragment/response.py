"""Response DTOs for app_config_fragment v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel, BaseRootResponseModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

__all__ = (
    "AppConfigFragmentBulkErrorInfo",
    "AppConfigFragmentNode",
    "AppConfigFragmentsByNamesPayload",
    "BulkPurgeAppConfigFragmentPayload",
    "PurgeAppConfigFragmentPayload",
    "SearchAppConfigFragmentPayload",
    "UpsertAppConfigFragmentsPayload",
)


class AppConfigFragmentNode(BaseResponseModel):
    """Node model representing one app config fragment."""

    id: AppConfigFragmentID = Field(description="App config fragment id.")
    config_name: str = Field(description="Config name the fragment belongs to.")
    scope_type: AppConfigScopeType = Field(description="Scope the fragment is written at.")
    scope_id: AppConfigScopeID | None = Field(
        description="Scope identifier: the domain id or user id; null for public scope."
    )
    config: dict[str, Any] = Field(description="The fragment's JSON config document.")
    created_at: datetime = Field(description="Creation timestamp (UTC).")
    updated_at: datetime = Field(description="Last update timestamp (UTC).")


class AppConfigFragmentsByNamesPayload(BaseRootResponseModel[list[AppConfigFragmentNode | None]]):
    """One entry per requested config name, null where the scope holds no fragment for it."""


class UpsertAppConfigFragmentsPayload(BaseResponseModel):
    """Payload for a scoped upsert of many fragments (all-or-nothing)."""

    items: list[AppConfigFragmentNode] = Field(description="The upserted app config fragments.")


class PurgeAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment purge."""

    id: AppConfigFragmentID = Field(description="Id of the purged app config fragment.")


class AppConfigFragmentBulkErrorInfo(BaseResponseModel):
    """One failed item of a partial-success bulk mutation."""

    id: AppConfigFragmentID = Field(description="Id of the fragment the failed item targeted.")
    message: str = Field(description="Reason the item failed.")


class BulkPurgeAppConfigFragmentPayload(BaseResponseModel):
    """Partial-success payload for a bulk fragment purge."""

    items: list[AppConfigFragmentID] = Field(description="Ids of successfully purged fragments.")
    failed: list[AppConfigFragmentBulkErrorInfo] = Field(
        description="Per-item failures, each naming the fragment it targeted."
    )


class SearchAppConfigFragmentPayload(BaseResponseModel):
    """Payload for paginated app config fragment search results."""

    items: list[AppConfigFragmentNode] = Field(description="App config fragment nodes.")
    total_count: int = Field(description="Total count matching the query.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
