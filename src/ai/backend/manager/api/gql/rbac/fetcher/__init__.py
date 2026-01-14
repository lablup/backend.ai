"""RBAC fetcher package."""

from .role import (
    fetch_role,
    fetch_roles,
    get_role_pagination_spec,
)

__all__ = [
    "fetch_role",
    "fetch_roles",
    "get_role_pagination_spec",
]
