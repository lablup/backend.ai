"""Request DTOs for Login Session DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter

from .types import LoginSessionOrderField, LoginSessionStatus, OrderDirection

__all__ = (
    "AdminRevokeLoginSessionInput",
    "AdminSearchLoginSessionsInput",
    "LoginSessionFilter",
    "LoginSessionOrder",
    "LoginSessionStatusFilter",
    "MyRevokeLoginSessionInput",
    "MySearchLoginSessionsInput",
)


class LoginSessionStatusFilter(BaseRequestModel):
    """Filter for login session status."""

    equals: LoginSessionStatus | None = Field(default=None, description="Exact status match")
    in_: list[LoginSessionStatus] | None = Field(
        default=None, alias="in", description="Status is in list"
    )
    not_in: list[LoginSessionStatus] | None = Field(
        default=None, description="Status is not in list"
    )


class LoginSessionFilter(BaseRequestModel):
    """Filter for login sessions."""

    status: LoginSessionStatusFilter | None = Field(default=None, description="Status filter")
    access_key: StringFilter | None = Field(default=None, description="Access key filter")
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter sessions by created_at datetime"
    )
    last_accessed_at: DateTimeFilter | None = Field(
        default=None, description="Filter sessions by last_accessed_at datetime"
    )
    AND: list[LoginSessionFilter] | None = Field(
        default=None, description="All conditions must match"
    )
    OR: list[LoginSessionFilter] | None = Field(
        default=None, description="At least one condition must match"
    )
    NOT: list[LoginSessionFilter] | None = Field(
        default=None, description="None of the conditions must match"
    )


LoginSessionFilter.model_rebuild()


class LoginSessionOrder(BaseRequestModel):
    """Ordering specification for login sessions."""

    field: LoginSessionOrderField
    direction: OrderDirection = OrderDirection.DESC


class AdminSearchLoginSessionsInput(BaseRequestModel):
    """Input for searching login sessions (admin)."""

    filter: LoginSessionFilter | None = Field(default=None, description="Filter criteria")
    order: list[LoginSessionOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")


class MySearchLoginSessionsInput(BaseRequestModel):
    """Input for searching login sessions (current user)."""

    filter: LoginSessionFilter | None = Field(default=None, description="Filter criteria")
    order: list[LoginSessionOrder] | None = Field(default=None, description="Sort order")
    first: int | None = Field(default=None, ge=1, description="Cursor-forward page size")
    after: str | None = Field(default=None, description="Cursor-forward start cursor")
    last: int | None = Field(default=None, ge=1, description="Cursor-backward page size")
    before: str | None = Field(default=None, description="Cursor-backward end cursor")
    limit: int | None = Field(default=None, ge=1, description="Offset-based page size")
    offset: int | None = Field(default=None, ge=0, description="Offset-based page offset")


class MyRevokeLoginSessionInput(BaseRequestModel):
    """Input for revoking a login session (current user)."""

    session_id: UUID = Field(description="ID of the login session to revoke")


class AdminRevokeLoginSessionInput(BaseRequestModel):
    """Input for revoking a login session (admin)."""

    session_id: UUID = Field(description="ID of the login session to revoke")
