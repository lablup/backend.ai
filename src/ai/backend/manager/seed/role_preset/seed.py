from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any, Self, override

from pydantic import field_validator, model_validator

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType, GlobalEntityType
from ai.backend.common.data.permission.types import Permission, role_scope_types
from ai.backend.manager.models.rbac_models.role_permission_preset.purgers import (
    RolePermissionPresetUngrantedPurger,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.upserters import (
    RolePermissionPresetUpserter,
)
from ai.backend.manager.models.rbac_models.role_preset.upserters import RolePresetUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection
from ai.backend.manager.seed.role_preset.check import RoleSeedChecker
from ai.backend.manager.seed.role_preset.kinds import PermissionKinds

# The vocabulary a role file writes an operation with, one name per permission bit.
_OPERATION_NAMES: dict[str, Permission] = {
    "read": Permission.READ,
    "update": Permission.UPDATE,
    "create": Permission.CREATE,
    "soft_delete": Permission.SOFT_DELETE,
    "hard_delete": Permission.HARD_DELETE,
}


class RolePresetSeed(SeedItem):
    """One seed role, as its file states it.

    The header fields are the ``role_presets`` row. The id is stated rather than
    derived, so renaming a role leaves what points at it alone. ``scope`` names the one
    global entity a ``global`` role is created in. ``permissions`` lists every entity
    type, with an empty list where the role is granted nothing.
    """

    id: RolePresetID
    name: str
    scope_type: EntityType
    scope: GlobalEntityName | None = None
    auto_assign: bool
    permissions: dict[str, Permission]

    @field_validator("scope_type", mode="before")
    @classmethod
    def _known_scope(cls, value: Any) -> Any:
        """The scope a role is created in, refusing one no role sits in."""
        allowed = {str(scope) for scope in (*role_scope_types(), GlobalEntityType())}
        if value not in allowed:
            raise ValueError(f"{value!r} is not a role scope; one of {sorted(allowed)}")
        return EntityType(value)

    @model_validator(mode="after")
    def _scope_named_for_global(self) -> Self:
        """A ``global`` role names its scope; a role of any other type does not."""
        is_global = self.scope_type == GlobalEntityType()
        if is_global and self.scope is None:
            raise ValueError("a global role names its scope")
        if not is_global and self.scope is not None:
            raise ValueError(f"a {self.scope_type} role is created in every {self.scope_type}")
        return self

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

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        """The preset, one permission row per granted bit, and under an overwrite the
        rows on a stated entity type that the grant leaves out."""
        return SeedWrite(
            upserter=RolePresetUpserter(
                id=self.id,
                name=self.name,
                scope_type=self.scope_type,
                auto_assign=self.auto_assign,
            ),
            field_upserters=[
                RolePermissionPresetUpserter(entity_type=EntityType(entity_type), permission=bit)
                for entity_type, mask in sorted(self.granted().items())
                for bit in mask
            ],
            field_purgers=[
                RolePermissionPresetUngrantedPurger(
                    grants={
                        EntityType(entity_type): mask
                        for entity_type, mask in self.permissions.items()
                    }
                )
            ]
            if self.permissions
            else [],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[RolePresetSeed]]) -> list[SeedRejection]:
        sources_by_name: dict[str, set[str]] = defaultdict(set)
        for file in files:
            for seed in file.items:
                sources_by_name[seed.name].add(file.source)
        rejections: list[SeedRejection] = []
        seeds = [seed for file in files for seed in file.items]
        for finding in RoleSeedChecker(PermissionKinds(), seeds).findings():
            rejections.extend(
                SeedRejection(source, finding.render())
                for source in sorted(sources_by_name[finding.role])
            )
        return rejections
