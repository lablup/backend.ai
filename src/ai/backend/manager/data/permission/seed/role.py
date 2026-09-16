from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission, role_scope_types

# The vocabulary a role file writes an operation with, one name per permission bit.
_OPERATION_NAMES: dict[str, Permission] = {
    "read": Permission.READ,
    "update": Permission.UPDATE,
    "create": Permission.CREATE,
    "soft_delete": Permission.SOFT_DELETE,
    "hard_delete": Permission.HARD_DELETE,
}


class RoleSeed(BaseModel):
    """One seed role, as its file states it.

    The header fields are the ``role_presets`` row. The id is stated rather than
    derived, so renaming a role leaves what points at it alone. ``permissions`` lists
    every entity type, with an empty list where the role is granted nothing.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: RolePresetID
    name: str
    scope_type: EntityType
    auto_assign: bool
    permissions: dict[str, Permission]

    @field_validator("scope_type", mode="before")
    @classmethod
    def _known_scope(cls, value: Any) -> Any:
        """The scope a role is created in, refusing one no role sits in."""
        allowed = {str(scope) for scope in role_scope_types()}
        if value not in allowed:
            raise ValueError(f"{value!r} is not a role scope; one of {sorted(allowed)}")
        return EntityType(value)

    @model_validator(mode="before")
    @classmethod
    def _read_operations(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        stated = values.get("permissions")
        if not isinstance(stated, dict):
            return values
        values = dict(values)
        values["permissions"] = {
            kind: cls._mask(kind, operations) for kind, operations in stated.items()
        }
        return values

    @classmethod
    def _mask(cls, kind: str, operations: Any) -> Permission:
        if not isinstance(operations, list):
            raise ValueError(f"{kind}: expected a list of operations, got {operations!r}")
        mask = Permission.NONE
        seen: set[str] = set()
        for operation in operations:
            if operation in seen:
                raise ValueError(f"{kind}: {operation!r} is stated twice")
            bit = _OPERATION_NAMES.get(operation)
            if bit is None:
                raise ValueError(
                    f"{kind}: {operation!r} is not an operation; one of {sorted(_OPERATION_NAMES)}"
                )
            seen.add(operation)
            mask |= bit
        return mask

    def granted(self) -> dict[str, Permission]:
        """The entity types this role is granted at least one operation on."""
        return {
            kind: mask for kind, mask in self.permissions.items() if mask is not Permission.NONE
        }

    def covers(self, other: Self) -> bool:
        """Whether this role's grant includes every bit the other role holds."""
        return all(
            self.permissions.get(kind, Permission.NONE).covers(mask)
            for kind, mask in other.granted().items()
        )
