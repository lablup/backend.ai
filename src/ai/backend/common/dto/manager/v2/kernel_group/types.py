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
    "KernelGroupEnvironOrderField",
    "KernelGroupEnvironScope",
    "KernelGroupOrderField",
    "KernelGroupResourceSlotOrderField",
    "KernelGroupResourceSlotScope",
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


class KernelGroupEnvironOrderField(StrEnum):
    """Fields available for ordering kernel group environ rows."""

    KEY = "key"


class KernelGroupEnvironScope(BaseRequestModel):
    """Scope for the scoped kernel group environ query. At least one session must be given."""

    session: NonEmptyList[UUIDScope] = Field(
        description="Sessions whose kernel groups' environ rows are being read."
    )


class KernelGroupResourceSlotOrderField(StrEnum):
    """Fields available for ordering kernel group resource slot rows."""

    SLOT_NAME = "slot_name"


class KernelGroupResourceSlotScope(BaseRequestModel):
    """Scope for the scoped kernel group resource slot query. At least one session must be
    given."""

    session: NonEmptyList[UUIDScope] = Field(
        description="Sessions whose kernel groups' resource slot rows are being read."
    )
