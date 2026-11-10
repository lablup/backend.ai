"""The single-bit rule of ``permissions`` rows."""

from __future__ import annotations

from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.permission import InvalidPermissionOperation


def single_bit(permission: Permission) -> Permission:
    """``permission`` if it is exactly one operation bit; a row holds one.

    A grant operation has no bit, and a mask spans several rows, so neither
    can be stored as a permission.
    """
    if permission == Permission.NONE or permission & (permission - 1):
        raise InvalidPermissionOperation(
            f"{permission!r} is not a single operation bit; a permission row holds one."
        )
    return permission
