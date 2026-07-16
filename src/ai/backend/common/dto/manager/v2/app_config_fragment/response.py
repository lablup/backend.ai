"""Response DTOs for app_config_fragment v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.app_config.types import AppConfigScopeType

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

    id: UUID = Field(description="App config fragment UUID.")
    config_name: str = Field(description="Config name the fragment belongs to.")
    scope_type: AppConfigScopeType = Field(description="Scope the fragment is written at.")
    scope_id: str | None = Field(
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

    id: UUID = Field(description="UUID of the purged app config fragment.")


class AppConfigFragmentBulkErrorInfo(BaseResponseModel):
    """One failed item of a partial-success bulk mutation."""

    index: int = Field(description="Zero-based index of the failed item in the request batch.")
    message: str = Field(description="Reason the item failed.")


class BulkUpdateAppConfigFragmentPayload(BaseResponseModel):
    """Partial-success payload for a bulk fragment update."""

    succeeded: list[AppConfigFragmentNode] = Field(description="Successfully updated fragments.")
    failed: list[AppConfigFragmentBulkErrorInfo] = Field(
        description="Per-item failures with their batch index."
    )


class BulkPurgeAppConfigFragmentPayload(BaseResponseModel):
    """Partial-success payload for a bulk fragment purge."""

    purged_ids: list[UUID] = Field(description="Ids of successfully purged fragments.")
    failed: list[AppConfigFragmentBulkErrorInfo] = Field(
        description="Per-item failures with their batch index."
    )
