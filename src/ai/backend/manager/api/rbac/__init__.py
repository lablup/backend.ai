"""Backward-compatibility shim for the RBAC module.

Handler logic has been migrated to ``api.rest.rbac``.  This package
re-exports public names so that existing imports continue to work.

``create_app`` is lazily imported via ``__getattr__`` to avoid a
circular import with ``api.rest.rbac.handler`` which imports adapter
modules from this package.
"""

import importlib

from .assigned_user_adapter import AssignedUserAdapter
from .object_permission_adapter import ObjectPermissionAdapter
from .permission_adapter import PermissionAdapter
from .role_adapter import RoleAdapter

__all__ = (
    "AssignedUserAdapter",
    "ObjectPermissionAdapter",
    "PermissionAdapter",
    "RoleAdapter",
    "create_app",
)


def __getattr__(name: str) -> object:
    if name == "create_app":
        mod = importlib.import_module(".handler", __name__)
        return mod.create_app
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
