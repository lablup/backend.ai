"""
Request DTOs for AppConfig (merged view) DTO v2.
"""

from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter

from .types import AppConfigOrderField, OrderDirection

__all__ = (
    "AppConfigFilter",
    "AppConfigOrder",
    "AppConfigScope",
    "GetUserAppConfigInput",
    "ScopedSearchAppConfigsInput",
    "SearchAppConfigsInput",
)


class GetUserAppConfigInput(BaseRequestModel):
    """Input for reading a single merged AppConfig for a target user
    (admin path — the `my` variant resolves the user internally)."""

    user_id: UUID = Field(description="Target user's UUID.")
    name: str = Field(description="Policy / config name.")


class AppConfigFilter(BaseRequestModel):
    """Filter for AppConfig merged-view search.

    `created_at` / `updated_at` filter against the **oldest** /
    **latest** timestamp across the contributing fragments — the
    natural projection of "when was this config first created" and
    "when was it last touched".
    """

    name: StringFilter | None = Field(default=None, description="Filter by policy name.")
    user_id: UUIDFilter | None = Field(
        default=None,
        description="Filter by target user id (admin cross-user search only).",
    )
    created_at: DateTimeFilter | None = Field(
        default=None,
        description=("Filter by the oldest contributing fragment's creation timestamp."),
    )
    updated_at: DateTimeFilter | None = Field(
        default=None,
        description=("Filter by the latest contributing fragment's update timestamp."),
    )


class AppConfigOrder(BaseRequestModel):
    """Order specification for AppConfig merged-view results."""

    field: AppConfigOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class _AppConfigSearchInputBase(BaseRequestModel):
    filter: AppConfigFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AppConfigOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Maximum items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class AppConfigScope(BaseRequestModel):
    """Scope for the scoped merged-view AppConfig query (user_ids are OR'd)."""

    user_ids: list[UUID] = Field(
        description="Target user UUIDs to scope the merged-view search to.",
    )

    @model_validator(mode="after")
    def validate_non_empty(self) -> Self:
        if not self.user_ids:
            raise ValueError("AppConfigScope requires a non-empty 'user_ids'")
        return self


class ScopedSearchAppConfigsInput(_AppConfigSearchInputBase):
    """Input for scoped (user-restricted) merged-view AppConfig search.

    `scope.user_ids` are OR'd; non-admin callers are restricted to their
    own user by RBAC at the adapter / processor boundary. Replaces the
    former `my` variant — self-service is just a USER-scoped search.
    """

    scope: AppConfigScope = Field(description="Scope (OR across all user_ids).")


class SearchAppConfigsInput(_AppConfigSearchInputBase):
    """Input for admin cross-user merged-view search.

    Optional `filter.user_id` pins the search to a single user.
    """
