"""Common types for system session environ DTO v2."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "SystemSessionEnvironOrderField",
    "SystemSessionEnvironScope",
    "SystemSessionEnvironScopeInfo",
    "SystemSessionEnvironScopeType",
    "SystemSessionEnvironValueSource",
)


class SystemSessionEnvironOrderField(StrEnum):
    KEY = "key"
    VALUE_SOURCE = "value_source"
    SCOPE_TYPE = "scope_type"
    ENABLED = "enabled"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SystemSessionEnvironScopeInfo(BaseResponseModel):
    """The scope a system session environ row is bound to."""

    scope_type: SystemSessionEnvironScopeType = Field(
        description="Whether the row applies to every session, a domain's or a project's."
    )
    scope_id: SystemSessionEnvironScopeID = Field(
        description="The id of the public entity, the domain or the project the row is bound to."
    )


class SystemSessionEnvironScope(BaseRequestModel):
    """Scope for the scoped system session environ query.

    Each list is OR'd internally and across lists. Raises an error if every field is empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose rows are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose rows are being read"
    )
    public: bool = Field(default=False, description="Include the rows registered in public")

    @model_validator(mode="after")
    def _require_non_empty(self) -> SystemSessionEnvironScope:
        if not self.domain and not self.project and not self.public:
            raise ValueError(
                "SystemSessionEnvironScope requires a non-empty value for 'domain', 'project'"
                " or 'public'"
            )
        return self
