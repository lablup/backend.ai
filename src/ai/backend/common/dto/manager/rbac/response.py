"""
Response DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = ("DeleteRoleResponse",)


class DeleteRoleResponse(BaseResponseModel):
    """Response for deleting a role."""

    deleted: bool = Field(description="Whether the role was deleted")
