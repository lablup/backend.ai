"""RBAC GraphQL node types package."""

from .permission import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
    PermissionGroup,
    PermissionGroupConnection,
    PermissionGroupEdge,
    Scope,
    ScopedPermission,
    ScopedPermissionConnection,
    ScopedPermissionEdge,
)
from .role import (
    Role,
    RoleConnection,
    RoleEdge,
)

__all__ = [
    # Permission nodes
    "ObjectPermission",
    "ObjectPermissionConnection",
    "ObjectPermissionEdge",
    "PermissionGroup",
    "PermissionGroupConnection",
    "PermissionGroupEdge",
    "Scope",
    "ScopedPermission",
    "ScopedPermissionConnection",
    "ScopedPermissionEdge",
    # Role nodes
    "Role",
    "RoleConnection",
    "RoleEdge",
]
