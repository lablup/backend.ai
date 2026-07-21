"""Response DTOs for app_config_fragment v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

__all__ = (
    "AppConfigFragmentBulkErrorInfo",
    "AppConfigFragmentNode",
    "BulkPurgeAppConfigFragmentPayload",
    "BulkUpdateAppConfigFragmentPayload",
    "CreateAppConfigFragmentPayload",
    "PurgeAppConfigFragmentPayload",
    "UpdateAppConfigFragmentPayload",
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


class CreateAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment creation."""

    app_config_fragment: AppConfigFragmentNode = Field(description="Created app config fragment.")


class UpdateAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment update."""

    app_config_fragment: AppConfigFragmentNode = Field(description="Updated app config fragment.")


class PurgeAppConfigFragmentPayload(BaseResponseModel):
    """Payload for app config fragment purge."""

    id: AppConfigFragmentID = Field(description="Id of the purged app config fragment.")


class AppConfigFragmentBulkErrorInfo(BaseResponseModel):
    """One failed item of a partial-success bulk mutation."""

    id: AppConfigFragmentID = Field(description="Id of the fragment the failed item targeted.")
    message: str = Field(description="Reason the item failed.")


class BulkUpdateAppConfigFragmentPayload(BaseResponseModel):
    """Partial-success payload for a bulk fragment update."""

    items: list[AppConfigFragmentNode] = Field(description="Successfully updated fragments.")
    failed: list[AppConfigFragmentBulkErrorInfo] = Field(
        description="Per-item failures, each naming the fragment it targeted."
    )


class BulkPurgeAppConfigFragmentPayload(BaseResponseModel):
    """Partial-success payload for a bulk fragment purge."""

    items: list[AppConfigFragmentID] = Field(description="Ids of successfully purged fragments.")
    failed: list[AppConfigFragmentBulkErrorInfo] = Field(
        description="Per-item failures, each naming the fragment it targeted."
    )
