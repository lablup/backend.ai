"""Request DTOs for Login History DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter

from .types import LoginAttemptResult, LoginHistoryOrderField, OrderDirection

__all__ = (
    "AdminSearchLoginHistoryInput",
    "LoginHistoryFilter",
    "LoginHistoryOrder",
    "LoginHistoryResultFilter",
    "MySearchLoginHistoryInput",
)


class LoginHistoryResultFilter(BaseRequestModel):
    """Filter for login attempt result."""

    equals: LoginAttemptResult | None = Field(default=None, description="Exact result match")
    in_: list[LoginAttemptResult] | None = Field(
        default=None, alias="in", description="Result is in list"
    )
    not_in: list[LoginAttemptResult] | None = Field(
        default=None, description="Result is not in list"
    )


class LoginHistoryFilter(BaseRequestModel):
    """Filter for login history."""

    domain_name: StringFilter | None = Field(default=None, description="Domain name filter")
    result: LoginHistoryResultFilter | None = Field(
        default=None, description="Login attempt result filter"
    )
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter history by created_at datetime"
    )
    AND: list[LoginHistoryFilter] | None = Field(
        default=None, description="All conditions must match"
    )
    OR: list[LoginHistoryFilter] | None = Field(
        default=None, description="At least one condition must match"
    )
    NOT: list[LoginHistoryFilter] | None = Field(
        default=None, description="None of the conditions must match"
    )


LoginHistoryFilter.model_rebuild()


class LoginHistoryOrder(BaseRequestModel):
    """Ordering specification for login history."""

    field: LoginHistoryOrderField
    direction: OrderDirection = OrderDirection.DESC


class AdminSearchLoginHistoryInput(BaseRequestModel):
    """Input for searching login history (admin)."""

    filter: LoginHistoryFilter | None = Field(default=None, description="Filter criteria")
    order: list[LoginHistoryOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")


class MySearchLoginHistoryInput(BaseRequestModel):
    """Input for searching login history (current user)."""

    filter: LoginHistoryFilter | None = Field(default=None, description="Filter criteria")
    order: list[LoginHistoryOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")
