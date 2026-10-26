"""Response DTOs for system session environ DTO v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeInfo,
    SystemSessionEnvironSourceKind,
)

__all__ = (
    "AdminSearchSystemSessionEnvironsPayload",
    "ListSystemSessionEnvironValueSourcesPayload",
    "SystemSessionEnvironNode",
    "SystemSessionEnvironValueSourceNode",
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
    enabled: bool = Field(
        description="Whether the row is injected. A disabled row still hides the same key at a broader scope."
    )
    created_at: datetime = Field(description="When the row was created.")
    updated_at: datetime = Field(description="When the row was last changed.")


class AdminSearchSystemSessionEnvironsPayload(BaseResponseModel):
    """A page of system session environ rows."""

    items: list[SystemSessionEnvironNode] = Field(description="The rows on this page.")
    total_count: int = Field(description="Total number of rows matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class SystemSessionEnvironValueSourceNode(BaseResponseModel):
    """A value of a starting session a system session environ row can inject."""

    name: str = Field(description="The value source name a row carries in value_source.")
    kind: SystemSessionEnvironSourceKind = Field(
        description=(
            "Whether the value wins over the session's own environ (required) or loses to it "
            "(optional)."
        )
    )


class ListSystemSessionEnvironValueSourcesPayload(BaseResponseModel):
    """Every value source a system session environ row can carry."""

    items: list[SystemSessionEnvironValueSourceNode] = Field(description="The value sources.")
