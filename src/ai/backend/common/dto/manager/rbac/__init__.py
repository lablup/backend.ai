"""
Common DTOs for RBAC system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import CreateRoleRequest
from .response import CreateRoleResponse, RoleDTO
from .types import RoleSource, RoleStatus

__all__ = (
    # Types
    "RoleSource",
    "RoleStatus",
    # Request DTOs
    "CreateRoleRequest",
    # Response DTOs
    "RoleDTO",
    "CreateRoleResponse",
)
