from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope


class BootstrapScriptOrderField(StrEnum):
    """Fields available for ordering bootstrap scripts."""

    CREATED_AT = "created_at"


class BootstrapScriptScope(BaseRequestModel):
    """Scope for the scoped bootstrap script query; the items are OR'd."""

    user: list[UUIDScope] = Field(description="Users whose bootstrap scripts are being read.")

    @model_validator(mode="after")
    def _require_a_user(self) -> Self:
        if not self.user:
            raise ValueError("BootstrapScriptScope requires a non-empty 'user'")
        return self
