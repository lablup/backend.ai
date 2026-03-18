"""
Common types for group DTOs.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import enum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.deployment.types import OrderDirection


class GroupOrderField(enum.StrEnum):
    """Fields that can be used for ordering groups."""

    NAME = "name"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"


class GroupOrder(BaseRequestModel):
    """Order specification for groups."""

    field: GroupOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


__all__ = (
    "GroupOrder",
    "GroupOrderField",
)
