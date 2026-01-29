"""RBAC fetcher package."""

from .role import (
    fetch_role,
    fetch_role_object_permissions,
    fetch_role_scopes,
    fetch_roles,
    fetch_scope_permissions,
    get_role_pagination_spec,
)

__all__ = [
    "fetch_role",
    "fetch_role_object_permissions",
    "fetch_role_scopes",
    "fetch_roles",
    "fetch_scope_permissions",
    "get_role_pagination_spec",
]
