"""
Common types for resource group DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "OrderDirection",
    "PreemptionModeDTO",
    "ResourceGroupOrderDirection",
    "ResourceGroupOrderField",
    "ResourceGroupScope",
    "SchedulerTypeDTO",
)


class ResourceGroupOrderDirection(StrEnum):
    """Order direction for resource group sorting."""

    ASC = "ASC"
    DESC = "DESC"


class ResourceGroupOrderField(StrEnum):
    """Fields available for ordering resource groups."""

    NAME = "name"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"


class SchedulerTypeDTO(StrEnum):
    """Scheduler type for resource group."""

    FIFO = "fifo"
    LIFO = "lifo"
    DRF = "drf"
    FAIR_SHARE = "fair-share"


class PreemptionModeDTO(StrEnum):
    """How to preempt a session when preemption is triggered."""

    TERMINATE = "terminate"
    RESCHEDULE = "reschedule"


class ResourceGroupScope(BaseRequestModel):
    """Scope for the scoped resource group query.

    Each list is OR'd internally and across lists. Raises an error if every field is
    empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose resource groups are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose resource groups are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose resource groups are being read"
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> ResourceGroupScope:
        if not self.domain and not self.project and not self.user:
            raise ValueError(
                "ResourceGroupScope requires a non-empty value for 'domain', 'project' or 'user'"
            )
        return self
