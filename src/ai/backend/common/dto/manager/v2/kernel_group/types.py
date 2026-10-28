"""
Common types for KernelGroup DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import NonEmptyList
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "KernelGroupOrderField",
    "KernelGroupScope",
)


class KernelGroupOrderField(StrEnum):
    """Fields available for ordering kernel groups."""

    ROLE = "role"
    REQUESTED_STARTS_AT = "requested_starts_at"
    CREATED_AT = "created_at"


class KernelGroupScope(BaseRequestModel):
    """Scope for the scoped kernel group query. At least one session must be given."""

    session: NonEmptyList[UUIDScope] = Field(
        description="Sessions whose kernel groups are being read."
    )
