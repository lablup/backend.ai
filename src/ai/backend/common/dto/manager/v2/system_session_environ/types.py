"""Common types for system session environ DTO v2."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)

__all__ = (
    "SystemSessionEnvironOrderField",
    "SystemSessionEnvironScopeInfo",
    "SystemSessionEnvironScopeType",
    "SystemSessionEnvironValueSource",
)


class SystemSessionEnvironOrderField(StrEnum):
    KEY = "key"
    VALUE_SOURCE = "value_source"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"


class SystemSessionEnvironScopeInfo(BaseResponseModel):
    """The scope a system session environ row is bound to."""

    scope_type: SystemSessionEnvironScopeType = Field(
        description="Whether the row applies to every session, a domain's or a project's."
    )
    scope_id: SystemSessionEnvironScopeID = Field(
        description="The id of the public entity, the domain or the project the row is bound to."
    )
