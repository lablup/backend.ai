"""
Response DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AssignedUserDTO",
    "SearchUsersAssignedToRoleResponse",
    "PaginationInfo",
)


class AssignedUserDTO(BaseModel):
    """DTO for user assigned to a role."""

    user_id: UUID = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="User email")
    granted_by: Optional[UUID] = Field(default=None, description="ID of user who granted this role")
    granted_at: datetime = Field(description="Timestamp when the role was granted")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: Optional[int] = Field(default=None, description="Maximum items returned")


class SearchUsersAssignedToRoleResponse(BaseResponseModel):
    """Response for searching users assigned to a role."""

    users: list[AssignedUserDTO] = Field(description="List of assigned users")
    pagination: PaginationInfo = Field(description="Pagination information")
