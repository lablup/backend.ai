"""RBAC fetcher package."""

from .permission import (
    fetch_role_object_permissions,
    fetch_role_permission_groups,
    fetch_role_scoped_permissions,
)
from .role import (
    fetch_role,
    fetch_roles,
    get_role_pagination_spec,
)

__all__ = [
    "fetch_role",
    "fetch_roles",
    "get_role_pagination_spec",
    "fetch_role_scoped_permissions",
    "fetch_role_object_permissions",
    "fetch_role_permission_groups",
]
