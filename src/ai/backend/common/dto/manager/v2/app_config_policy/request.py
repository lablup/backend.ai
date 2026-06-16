"""
Request DTOs for app_config_policy DTO v2.
"""

from __future__ import annotations

from typing import Self

from pydantic import Field, field_validator, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.identifier.app_config_policy import AppConfigPolicyID

from .types import AppConfigPolicyOrderField, AppConfigScopeType, OrderDirection

__all__ = (
    "AdminBulkCreateAppConfigPolicyItemInput",
    "AdminBulkUpdateAppConfigPolicyItemInput",
    "AdminBulkCreateAppConfigPoliciesInput",
    "AdminBulkPurgeAppConfigPoliciesInput",
    "AdminBulkUpdateAppConfigPoliciesInput",
    "AdminSearchAppConfigPoliciesInput",
    "AppConfigPolicyFilter",
    "AppConfigPolicyOrder",
    "AppConfigPolicyScope",
    "ScopedSearchAppConfigPoliciesInput",
)


class AppConfigPolicyFilter(BaseRequestModel):
    """Filter for app-config policy search."""

    config_name: StringFilter | None = Field(default=None, description="Filter by config_name")
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by created_at")
    updated_at: DateTimeFilter | None = Field(default=None, description="Filter by updated_at")


class AppConfigPolicyOrder(BaseRequestModel):
    """Order specification for app-config policies."""

    field: AppConfigPolicyOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


# ── Bulk mutation inputs (bulk-only writes) ──────────────────────


class AdminBulkCreateAppConfigPolicyItemInput(BaseRequestModel):
    """Per-item input for `adminBulkCreateAppConfigPolicies`."""

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Unique, immutable policy name.",
    )
    scope_sources: list[AppConfigScopeType] = Field(
        description="Ordered scope chain (low → high merge priority).",
    )

    @field_validator("config_name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and ensure config_name is non-blank."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("config_name must not be blank after stripping whitespace")
        return stripped


class AdminBulkUpdateAppConfigPolicyItemInput(BaseRequestModel):
    """Per-item input for `adminBulkUpdateAppConfigPolicies` (config_name is immutable)."""

    id: AppConfigPolicyID = Field(description="Policy row id.")
    scope_sources: list[AppConfigScopeType] = Field(
        description="Ordered scope chain (low → high merge priority).",
    )


class AdminBulkCreateAppConfigPoliciesInput(BaseRequestModel):
    items: list[AdminBulkCreateAppConfigPolicyItemInput] = Field(description="Policies to create.")


class AdminBulkUpdateAppConfigPoliciesInput(BaseRequestModel):
    items: list[AdminBulkUpdateAppConfigPolicyItemInput] = Field(description="Policies to update.")


class AdminBulkPurgeAppConfigPoliciesInput(BaseRequestModel):
    ids: list[AppConfigPolicyID] = Field(description="Policy row ids to purge.")


class AdminSearchAppConfigPoliciesInput(BaseRequestModel):
    """Input for searching app-config policies system-wide (admin, no scope)."""

    filter: AppConfigPolicyFilter | None = Field(default=None, description="Filter conditions")
    order: list[AppConfigPolicyOrder] | None = Field(
        default=None, description="Order specifications"
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Maximum items to return")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip")


class AppConfigPolicyScope(BaseRequestModel):
    """Scope for the scoped app-config-policy query (config_names are OR'd)."""

    config_names: list[str] = Field(description="Policy config_names to scope the query to.")

    @model_validator(mode="after")
    def validate_non_empty(self) -> Self:
        if not self.config_names:
            raise ValueError("AppConfigPolicyScope requires a non-empty 'config_names'")
        return self


class ScopedSearchAppConfigPoliciesInput(BaseRequestModel):
    """Input for searching app-config policies under a scope."""

    scope: AppConfigPolicyScope = Field(description="Scope (OR across all config_names).")
    filter: AppConfigPolicyFilter | None = Field(default=None, description="Filter conditions")
    order: list[AppConfigPolicyOrder] | None = Field(
        default=None, description="Order specifications"
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Maximum items to return")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip")
