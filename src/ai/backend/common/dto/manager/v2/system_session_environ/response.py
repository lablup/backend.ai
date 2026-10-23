"""Response DTOs for system session environ DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScopeInfo,
    SystemSessionEnvironValueSource,
)

__all__ = (
    "ResolveSystemSessionEnvironPayload",
    "SystemSessionEnvironNode",
)


class SystemSessionEnvironNode(BaseResponseModel):
    """A system session environ row: the value it injects under its key at its scope."""

    entity_id: SystemSessionEnvironID = Field(description="The id of the row.")
    key: str = Field(description="The environment variable name the value is injected under.")
    value_source: SystemSessionEnvironValueSource = Field(
        description="Which value of the starting session is injected."
    )
    scope: SystemSessionEnvironScopeInfo = Field(description="The scope the row is bound to.")


class ResolveSystemSessionEnvironPayload(BaseResponseModel):
    """The rows a session in the domain and project receives, one per key."""

    items: list[SystemSessionEnvironNode] = Field(
        description="Per key the enabled row at the most specific scope: project, domain, then public."
    )
