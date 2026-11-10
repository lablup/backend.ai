"""
Common types for SessionGroup DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.exception import InvalidAPIParameters

__all__ = (
    "SessionGroupOrderField",
    "SessionGroupPlacementDirectionEnum",
    "SessionGroupPlacementEnforcementEnum",
    "SessionGroupScope",
)


class SessionGroupPlacementDirectionEnum(StrEnum):
    """How the member sessions of a group sit relative to each other, per agent."""

    SPREAD = "spread"
    PACK = "pack"
    NONE = "none"


class SessionGroupPlacementEnforcementEnum(StrEnum):
    """How hard the placement direction is enforced when it cannot be satisfied."""

    PREFERRED = "preferred"
    STRICT = "strict"


class SessionGroupOrderField(StrEnum):
    """Fields available for ordering session groups."""

    PLACEMENT_DIRECTION = "placement_direction"
    PLACEMENT_ENFORCEMENT = "placement_enforcement"
    CREATED_AT = "created_at"
    DELETED_AT = "deleted_at"


class SessionGroupScope(BaseRequestModel):
    """Scope for the scoped session group query.

    Each list is OR'd internally and across lists; at least one must be given.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose session groups are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose session groups are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose session groups are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> SessionGroupScope:
        if not self.domain and not self.project and not self.user:
            raise InvalidAPIParameters(
                "SessionGroupScope requires a non-empty value for 'domain', 'project' or 'user'"
            )
        return self
