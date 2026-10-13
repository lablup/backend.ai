from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.data.permission.types import Permission


class PermissionOperations:
    """The vocabulary a role file writes an operation with, one name per permission bit."""

    _names: Mapping[str, Permission]

    def __init__(self) -> None:
        self._names = {
            "read": Permission.READ,
            "update": Permission.UPDATE,
            "create": Permission.CREATE,
            "soft_delete": Permission.SOFT_DELETE,
            "hard_delete": Permission.HARD_DELETE,
        }

    def read_permissions(self, values: Any) -> Any:
        """The item with its ``permissions`` lists read into masks, for a ``before``
        validator; anything else is left for the model to refuse."""
        if not isinstance(values, dict):
            return values
        stated = values.get("permissions")
        if not isinstance(stated, dict):
            return values
        return {
            **values,
            "permissions": {
                kind: self._mask(kind, operations) for kind, operations in stated.items()
            },
        }

    def _mask(self, kind: str, operations: Any) -> Permission:
        if not isinstance(operations, list):
            raise ValueError(f"{kind}: expected a list of operations, got {operations!r}")
        mask = Permission.NONE
        seen: set[str] = set()
        for operation in operations:
            if operation in seen:
                raise ValueError(f"{kind}: {operation!r} is stated twice")
            bit = self._names.get(operation)
            if bit is None:
                raise ValueError(
                    f"{kind}: {operation!r} is not an operation; one of {sorted(self._names)}"
                )
            seen.add(operation)
            mask |= bit
        return mask
