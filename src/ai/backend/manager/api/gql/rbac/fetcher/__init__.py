"""RBAC GQL fetcher module."""

from __future__ import annotations

from .permission import (
    fetch_permissions,
    get_permission_pagination_spec,
)
from .role import (
    fetch_role,
    fetch_role_assignments,
    fetch_roles,
    get_role_assignment_pagination_spec,
    get_role_pagination_spec,
)

__all__ = [
    # Permission
    "fetch_permissions",
    "get_permission_pagination_spec",
    # Role
    "fetch_role",
    "fetch_roles",
    "fetch_role_assignments",
    "get_role_pagination_spec",
    "get_role_assignment_pagination_spec",
]
