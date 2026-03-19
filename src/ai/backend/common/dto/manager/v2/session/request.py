"""
Request DTOs for Session v2 API.

Input models for session search, lifecycle actions, and service management.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import DateTimeRangeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.session.types import (
    OrderDirection,
    SessionOrderField,
    SessionStatusFilter,
)

__all__ = (
    "AdminSearchSessionsInput",
    "CommitSessionInput",
    "DestroySessionInput",
    "DownloadFilesInput",
    "ExecuteInput",
    "GetContainerLogsInput",
    "ListFilesInput",
    "RenameSessionInput",
    "RestartSessionInput",
    "SearchSessionsInput",
    "SessionFilter",
    "SessionOrder",
    "SessionPathParam",
    "ShutdownServiceInput",
    "StartServiceInput",
    "UploadFilesInput",
)


# ---------------------------------------------------------------------------
# Path parameter
# ---------------------------------------------------------------------------


class SessionPathParam(BaseRequestModel):
    """Path parameter for session-scoped endpoints."""

    session_name: str


# ---------------------------------------------------------------------------
# Search / query
# ---------------------------------------------------------------------------


class SessionFilter(BaseRequestModel):
    """Filter criteria for session listing."""

    id: UUIDFilter | None = None
    status: SessionStatusFilter | None = None
    name: StringFilter | None = None
    domain_name: StringFilter | None = None
    project_id: UUIDFilter | None = None
    user_uuid: UUIDFilter | None = None
    created_at: DateTimeRangeFilter | None = None
    AND: list[SessionFilter] | None = None
    OR: list[SessionFilter] | None = None
    NOT: list[SessionFilter] | None = None


SessionFilter.model_rebuild()


class SessionOrder(BaseRequestModel):
    """Ordering specification for session listing."""

    field: SessionOrderField
    direction: OrderDirection


class SearchSessionsInput(BaseRequestModel):
    """Input for paginated session search."""

    filter: SessionFilter | None = None
    order: SessionOrder | None = None
    limit: int = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)
    offset: int = Field(default=0, ge=0)


class AdminSearchSessionsInput(BaseRequestModel):
    """Input for admin search of sessions with cursor and offset pagination."""

    filter: SessionFilter | None = Field(default=None, description="Filter conditions.")
    order: list[SessionOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


class RestartSessionInput(BaseRequestModel):
    """Input for restarting a session."""

    owner_access_key: str | None = None


class DestroySessionInput(BaseRequestModel):
    """Input for destroying a session."""

    forced: bool = False
    recursive: bool = False
    owner_access_key: str | None = None


# ---------------------------------------------------------------------------
# Commit / imagify
# ---------------------------------------------------------------------------


class CommitSessionInput(BaseRequestModel):
    """Input for committing a session to an image snapshot."""

    login_session_token: str | None = None
    filename: str | None = None


# ---------------------------------------------------------------------------
# Code execution
# ---------------------------------------------------------------------------


class ExecuteInput(BaseRequestModel):
    """Input for executing code in a session kernel."""

    mode: str | None = None
    run_id: str | None = None
    code: str | None = None
    options: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Service management
# ---------------------------------------------------------------------------


class StartServiceInput(BaseRequestModel):
    """Input for starting an app service within a session."""

    app: str
    port: int | None = Field(default=None, ge=1024, le=65535)
    envs: str | None = None
    arguments: str | None = None
    login_session_token: str | None = None


class ShutdownServiceInput(BaseRequestModel):
    """Input for shutting down an app service within a session."""

    service_name: str


# ---------------------------------------------------------------------------
# Session rename
# ---------------------------------------------------------------------------


class RenameSessionInput(BaseRequestModel):
    """Input for renaming a session."""

    name: str = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


class DownloadFilesInput(BaseRequestModel):
    """Input for downloading files from a session."""

    files: list[str]


class UploadFilesInput(BaseRequestModel):
    """Input for uploading files to a session (multipart body; path param only)."""


class ListFilesInput(BaseRequestModel):
    """Input for listing files in a session."""

    path: str = "."


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


class GetContainerLogsInput(BaseRequestModel):
    """Input for retrieving container logs from a session."""

    owner_access_key: str | None = None
    kernel_id: UUID | None = None
