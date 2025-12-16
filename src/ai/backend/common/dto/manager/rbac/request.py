"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel

from .types import RoleSource, RoleStatus

__all__ = ("UpdateRoleRequest",)


class UpdateRoleRequest(BaseRequestModel):
    """Request to update a role."""

    name: Optional[str] = Field(default=None, description="Updated role name")
    source: Optional[RoleSource] = Field(default=None, description="Updated role source")
    status: Optional[RoleStatus] = Field(default=None, description="Updated role status")
    description: Optional[str | Sentinel] = Field(
        default=SENTINEL, description="Updated role description"
    )
