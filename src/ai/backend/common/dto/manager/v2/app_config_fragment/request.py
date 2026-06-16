"""
Request DTOs for app_config_fragment DTO v2.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import AppConfigFragmentOrderField, AppConfigScopeType, OrderDirection

__all__ = (
    "AdminAppConfigFragmentItemInput",
    "AdminBulkCreateAppConfigFragmentsInput",
    "AdminBulkPurgeAppConfigFragmentsInput",
    "AdminBulkUpdateAppConfigFragmentsInput",
    "AppConfigFragmentFilter",
    "AppConfigFragmentKeyInput",
    "AppConfigFragmentOrder",
    "MyBulkCreateAppConfigFragmentsInput",
    "MyBulkUpdateAppConfigFragmentsInput",
    "MyAppConfigFragmentItemInput",
    "SearchAppConfigFragmentsInput",
)


class AppConfigFragmentKeyInput(BaseRequestModel):
    """Natural-key identifier for a single fragment row."""

    scope_type: AppConfigScopeType = Field(description="Scope type.")
    scope_id: str = Field(description="Scope id (e.g., domain name, user id, or `public`).")
    name: str = Field(
        min_length=1,
        max_length=128,
        description="Policy name.",
    )


class AppConfigFragmentFilter(BaseRequestModel):
    """Filter for app-config fragment search."""

    id: UUIDFilter | None = Field(default=None, description="Filter by row id.")
    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    scope_type: AppConfigScopeType | None = Field(default=None, description="Filter by scope_type.")
    scope_id: StringFilter | None = Field(default=None, description="Filter by scope_id.")


class AppConfigFragmentOrder(BaseRequestModel):
    """Order specification for app-config fragments."""

    field: AppConfigFragmentOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


# ── Bulk mutation inputs ─────────────────────────────────────────


class AdminAppConfigFragmentItemInput(BaseRequestModel):
    """Per-item input for admin bulk create / update (natural key + payload)."""

    key: AppConfigFragmentKeyInput = Field(description="Natural-key identifier.")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw configuration payload (empty dict clears the row).",
    )


class AdminBulkCreateAppConfigFragmentsInput(BaseRequestModel):
    items: list[AdminAppConfigFragmentItemInput] = Field(description="Rows to create.")


class AdminBulkUpdateAppConfigFragmentsInput(BaseRequestModel):
    items: list[AdminAppConfigFragmentItemInput] = Field(description="Rows to update.")


class AdminBulkPurgeAppConfigFragmentsInput(BaseRequestModel):
    keys: list[AppConfigFragmentKeyInput] = Field(description="Natural keys to purge.")


class MyAppConfigFragmentItemInput(BaseRequestModel):
    """Per-item input for self-service (`my`) bulk — `scope_type`
    / `scope_id` are server-injected, so `name` is the only identifier.
    """

    name: str = Field(description="Policy name.")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw configuration payload (empty dict clears the row).",
    )


class MyBulkCreateAppConfigFragmentsInput(BaseRequestModel):
    items: list[MyAppConfigFragmentItemInput] = Field(description="USER-scope rows to create.")


class MyBulkUpdateAppConfigFragmentsInput(BaseRequestModel):
    items: list[MyAppConfigFragmentItemInput] = Field(description="USER-scope rows to update.")


class SearchAppConfigFragmentsInput(BaseRequestModel):
    """Input for searching fragments (raw rows) with filter / order / pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: AppConfigFragmentFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AppConfigFragmentOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Maximum items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")
