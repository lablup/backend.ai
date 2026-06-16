"""
Response DTOs for app_config_policy DTO v2.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID

__all__ = (
    "AdminBulkCreateAppConfigPoliciesPayload",
    "AdminBulkPurgeAppConfigPoliciesPayload",
    "AdminBulkUpdateAppConfigPoliciesPayload",
    "AppConfigPolicyBulkError",
    "AppConfigPolicyNode",
    "GetAppConfigPolicyPayload",
    "SearchAppConfigPoliciesPayload",
)


class AppConfigPolicyNode(BaseResponseModel):
    """Node representing a single app-config policy."""

    id: AppConfigPolicyID = Field(description="Policy row ID")
    config_name: str = Field(description="Unique, immutable policy name.")
    scope_sources: list[AppConfigScopeType] = Field(
        description="Ordered scope chain (low → high merge priority).",
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class GetAppConfigPolicyPayload(BaseResponseModel):
    """Payload returned after reading a single app-config policy by config_name."""

    item: AppConfigPolicyNode = Field(description="Policy data.")


class SearchAppConfigPoliciesPayload(BaseResponseModel):
    """Payload for paginated app-config policy search results."""

    items: list[AppConfigPolicyNode] = Field(description="Policies matching the filter.")
    total_count: int = Field(description="Total number of policies matching the filter.")
    has_next_page: bool = Field(default=False, description="Whether there is a next page.")
    has_previous_page: bool = Field(default=False, description="Whether there is a previous page.")


# ── Bulk mutation payloads (bulk-only writes) ────────────────────


class AppConfigPolicyBulkError(BaseResponseModel):
    """Per-item failure info for bulk Policy mutations."""

    index: int = Field(description="Original position in the input list.")
    message: str = Field(description="Reason for the failure.")


class AdminBulkCreateAppConfigPoliciesPayload(BaseResponseModel):
    """Payload for `adminBulkCreateAppConfigPolicies`."""

    created: list[AppConfigPolicyNode] = Field(description="Created policies.")
    failed: list[AppConfigPolicyBulkError] = Field(description="Per-item failures.")


class AdminBulkUpdateAppConfigPoliciesPayload(BaseResponseModel):
    """Payload for `adminBulkUpdateAppConfigPolicies`."""

    updated: list[AppConfigPolicyNode] = Field(description="Updated policies.")
    failed: list[AppConfigPolicyBulkError] = Field(description="Per-item failures.")


class AdminBulkPurgeAppConfigPoliciesPayload(BaseResponseModel):
    """Payload for `adminBulkPurgeAppConfigPolicies`."""

    purged_ids: list[AppConfigPolicyID] = Field(
        description="Ids of policies actually removed (absent ids no-oped).",
    )
    failed: list[AppConfigPolicyBulkError] = Field(description="Per-item failures.")
