"""
Common DTOs for RBAC system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import AssignRoleRequest
from .response import AssignRoleResponse

__all__ = (
    "AssignRoleRequest",
    "AssignRoleResponse",
)
