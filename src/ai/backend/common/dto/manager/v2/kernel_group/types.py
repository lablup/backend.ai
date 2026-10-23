"""
Common types for KernelGroup DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.exception import InvalidAPIParameters

__all__ = (
    "KernelGroupOrderField",
    "KernelGroupScope",
)


class KernelGroupOrderField(StrEnum):
    """Fields available for ordering kernel groups."""

    ROLE = "role"
    CREATED_AT = "created_at"


class KernelGroupScope(BaseRequestModel):
    """Scope for the scoped kernel group query. At least one session must be given."""

    session: list[UUIDScope] = Field(description="Sessions whose kernel groups are being read.")

    @model_validator(mode="after")
    def _require_non_empty(self) -> Self:
        if not self.session:
            raise InvalidAPIParameters("KernelGroupScope requires a non-empty value for 'session'")
        return self
