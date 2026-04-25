"""
Response DTOs for app_config_policy DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminBulkCreateAppConfigPoliciesPayload",
    "AdminBulkPurgeAppConfigPoliciesPayload",
    "AdminBulkUpdateAppConfigPoliciesPayload",
    "AppConfigPolicyBulkError",
    "AppConfigPolicyNode",
    "CreateAppConfigPolicyPayload",
    "GetAppConfigPolicyPayload",
    "PurgeAppConfigPolicyPayload",
    "SearchAppConfigPoliciesPayload",
    "UpdateAppConfigPolicyPayload",
)


class AppConfigPolicyNode(BaseResponseModel):
    """Node representing a single app-config policy (BEP-1052 §1)."""

    id: UUID = Field(description="Policy row ID")
    config_name: str = Field(description="Unique, immutable policy name.")
    scope_sources: list[str] = Field(
        description="Ordered scope chain (low → high merge priority).",
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class CreateAppConfigPolicyPayload(BaseResponseModel):
    """Payload returned after creating an app-config policy."""

    item: AppConfigPolicyNode = Field(description="Created policy.")


class UpdateAppConfigPolicyPayload(BaseResponseModel):
    """Payload returned after updating an app-config policy."""

    item: AppConfigPolicyNode = Field(description="Updated policy.")


class PurgeAppConfigPolicyPayload(BaseResponseModel):
    """Payload returned after purging an app-config policy."""

    config_name: str = Field(description="`config_name` of the purged policy.")
    purged: bool = Field(description="Whether a row was actually removed.")


class GetAppConfigPolicyPayload(BaseResponseModel):
    """Payload returned after reading a single app-config policy by config_name."""

    item: AppConfigPolicyNode | None = Field(default=None, description="Policy data, or null.")


class SearchAppConfigPoliciesPayload(BaseResponseModel):
    """Payload for paginated app-config policy search results."""

    items: list[AppConfigPolicyNode] = Field(description="Policies matching the filter.")
    total_count: int = Field(description="Total number of policies matching the filter.")
    has_next_page: bool = Field(default=False, description="Whether there is a next page.")
    has_previous_page: bool = Field(default=False, description="Whether there is a previous page.")


# ── Bulk mutation payloads (BEP-1052 §3) ─────────────────────────


class AppConfigPolicyBulkError(BaseResponseModel):
    """Per-item failure info for bulk Policy mutations."""

    index: int = Field(description="Original position in the input list.")
    config_name: str = Field(description="`config_name` of the failed row.")
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

    purged_config_names: list[str] = Field(
        description="`config_name`s of policies actually removed (absent names no-oped).",
    )
    failed: list[AppConfigPolicyBulkError] = Field(description="Per-item failures.")
