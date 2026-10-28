"""Response DTOs for system session environ DTO v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeInfo,
)

__all__ = (
    "AdminSearchSystemSessionEnvironsPayload",
    "CreateSystemSessionEnvironPayload",
    "DeleteSystemSessionEnvironPayload",
    "ListSystemSessionEnvironValueSourcesPayload",
    "PurgeSystemSessionEnvironPayload",
    "RestoreSystemSessionEnvironPayload",
    "SystemSessionEnvironNode",
    "UpdateSystemSessionEnvironPayload",
)


class SystemSessionEnvironNode(BaseResponseModel):
    """A system session environ row: the value it injects under its key at its scope."""

    entity_id: SystemSessionEnvironID = Field(description="The id of the row.")
    key: str = Field(description="The environment variable name the value is injected under.")
    value_source: str = Field(
        description=(
            "Which value of the starting session is injected, as a value source name "
            "the value source query lists."
        )
    )
    scope: SystemSessionEnvironScopeInfo = Field(description="The scope the row is bound to.")
    created_at: datetime = Field(description="When the row was created.")
    updated_at: datetime = Field(description="When the row was last changed.")
    deleted_at: datetime | None = Field(
        default=None,
        description="When the row was soft-deleted, or null if it is not.",
    )


class AdminSearchSystemSessionEnvironsPayload(BaseResponseModel):
    """A page of system session environ rows."""

    items: list[SystemSessionEnvironNode] = Field(description="The rows on this page.")
    total_count: int = Field(description="Total number of rows matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class ListSystemSessionEnvironValueSourcesPayload(BaseResponseModel):
    """Every value source a system session environ row can carry."""

    items: list[str] = Field(description="The value source names a row can carry.")


class CreateSystemSessionEnvironPayload(BaseResponseModel):
    """The system session environ row the create made."""

    system_session_environ: SystemSessionEnvironNode = Field(description="The created row.")


class UpdateSystemSessionEnvironPayload(BaseResponseModel):
    """The system session environ row after the update."""

    system_session_environ: SystemSessionEnvironNode = Field(description="The updated row.")


class DeleteSystemSessionEnvironPayload(BaseResponseModel):
    """The system session environ row after the soft delete."""

    system_session_environ: SystemSessionEnvironNode = Field(description="The soft-deleted row.")


class RestoreSystemSessionEnvironPayload(BaseResponseModel):
    """The system session environ row after the restore."""

    system_session_environ: SystemSessionEnvironNode = Field(description="The restored row.")


class PurgeSystemSessionEnvironPayload(BaseResponseModel):
    """The id of the system session environ row the purge removed."""

    entity_id: SystemSessionEnvironID = Field(description="The id of the purged row.")
