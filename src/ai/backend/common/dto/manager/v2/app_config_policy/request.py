"""
Request DTOs for app_config_policy DTO v2.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import AppConfigPolicyOrderField, OrderDirection

__all__ = (
    "AdminAppConfigPolicyItemInput",
    "AdminBulkCreateAppConfigPoliciesInput",
    "AdminBulkPurgeAppConfigPoliciesInput",
    "AdminBulkUpdateAppConfigPoliciesInput",
    "AppConfigPolicyFilter",
    "AppConfigPolicyOrder",
    "CreateAppConfigPolicyInput",
    "PurgeAppConfigPolicyInput",
    "SearchAppConfigPoliciesInput",
    "UpdateAppConfigPolicyInput",
)


class CreateAppConfigPolicyInput(BaseRequestModel):
    """Input for creating an app-config policy.

    `config_name` is immutable once created (BEP-1052 §1) and is the
    FK target referenced by `app_config_fragments.name`.
    """

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Unique, immutable policy name (doubles as the merge document key).",
    )
    scope_sources: list[str] = Field(
        description=(
            "Ordered scope chain (low → high merge priority) matching `AppConfigScopeType` values."
        ),
    )

    @field_validator("config_name")
    @classmethod
    def config_name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("config_name must not be blank or whitespace-only")
        return stripped


class UpdateAppConfigPolicyInput(BaseRequestModel):
    """Input for updating an app-config policy.

    Only `scope_sources` is mutable — `config_name` is fixed per
    BEP-1052 §1 and therefore identifies the target instead of
    appearing as a settable field.
    """

    config_name: str = Field(
        description="Target policy's `config_name` (immutable identifier).",
    )
    scope_sources: list[str] = Field(
        description="Replacement ordered scope chain.",
    )


class PurgeAppConfigPolicyInput(BaseRequestModel):
    """Input for purging (hard-delete) an app-config policy."""

    config_name: str = Field(description="`config_name` of the policy to purge.")


class AppConfigPolicyFilter(BaseRequestModel):
    """Filter for app-config policy search."""

    config_name: StringFilter | None = Field(default=None, description="Filter by config_name")


class AppConfigPolicyOrder(BaseRequestModel):
    """Order specification for app-config policies."""

    field: AppConfigPolicyOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


# ── Bulk mutation inputs (BEP-1052 §3) ───────────────────────────


class AdminAppConfigPolicyItemInput(BaseRequestModel):
    """Per-item input for `adminBulkCreate/UpdateAppConfigPolicies`.

    `user_writable` is intentionally omitted — user writes are blocked
    in this iteration; re-add when user writes are enabled (BEP-1052 §1).
    """

    config_name: str = Field(
        min_length=1,
        max_length=128,
        description="Unique, immutable policy name.",
    )
    scope_sources: list[str] = Field(
        description="Ordered scope chain (low → high merge priority).",
    )


class AdminBulkCreateAppConfigPoliciesInput(BaseRequestModel):
    items: list[AdminAppConfigPolicyItemInput] = Field(description="Policies to create.")


class AdminBulkUpdateAppConfigPoliciesInput(BaseRequestModel):
    items: list[AdminAppConfigPolicyItemInput] = Field(description="Policies to update.")


class AdminBulkPurgeAppConfigPoliciesInput(BaseRequestModel):
    config_names: list[str] = Field(description="`config_name`s to purge.")


class SearchAppConfigPoliciesInput(BaseRequestModel):
    """Input for searching app-config policies with filter / order / pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

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
