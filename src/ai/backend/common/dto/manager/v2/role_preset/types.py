"""Types for role preset v2 DTOs."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "RolePresetOrderField",
    "RolePresetUsage",
    "RolePresetUsedBy",
)


class RolePresetOrderField(StrEnum):
    """Fields available for ordering role presets."""

    NAME = "name"
    SCOPE_TYPE = "scope_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RolePresetUsedBy(BaseRequestModel):
    """Entities whose use of the preset narrows the result."""

    role: list[UUID] | None = Field(default=None, description="Roles instantiated from the preset")


class RolePresetUsage(BaseRequestModel):
    """Uses narrowing the presets read; every id is AND-ed.

    An entity the caller cannot read refuses the request.
    """

    used_by: RolePresetUsedBy | None = Field(
        default=None, description="Entities whose use of the preset narrows the result"
    )
