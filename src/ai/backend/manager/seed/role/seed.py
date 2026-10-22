from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Sequence
from typing import Any, override

from pydantic import Field, field_validator, model_validator

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission, role_scope_types
from ai.backend.manager.models.rbac_models.permission.purgers import (
    RolePermissionUngrantedPurger,
)
from ai.backend.manager.models.rbac_models.permission.upserters import RolePermissionUpserter
from ai.backend.manager.models.rbac_models.role.upserters import RoleUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection
from ai.backend.manager.seed.role_preset.kinds import PermissionKinds
from ai.backend.manager.seed.role_preset.operations import PermissionOperations


class RoleSeed(SeedItem):
    """One ``roles`` row in its scope, its ``permissions`` rows and its ``user_roles`` rows.

    ``permissions`` maps an entity type to the operations granted on every field of it.
    ``users`` are granted the role as the system grants it."""

    id: RoleID
    name: str = Field(min_length=1, max_length=64)
    description: str | None = None
    scope_type: EntityType
    scope_id: uuid.UUID
    role_preset_id: RolePresetID | None = None
    auto_assign: bool = False
    permissions: dict[str, Permission] = {}
    users: list[UserID] = []

    @field_validator("scope_type", mode="before")
    @classmethod
    def _known_scope(cls, value: Any) -> Any:
        allowed = {str(scope) for scope in role_scope_types()}
        if value not in allowed:
            raise ValueError(f"{value!r} is not a role scope; one of {sorted(allowed)}")
        return EntityType(value)

    @model_validator(mode="before")
    @classmethod
    def _read_operations(cls, values: Any) -> Any:
        return PermissionOperations().read_permissions(values)

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        """The role, one permission row per granted bit, its grants, and under an
        overwrite the permission rows on a stated entity type that the grant leaves out."""
        return SeedWrite(
            upserter=RoleUpserter(
                id=self.id,
                name=self.name,
                description=self.description,
                scope=RuntimeEntityID(self.scope_type, self.scope_id),
                role_preset_id=self.role_preset_id,
                auto_assign=self.auto_assign,
            ),
            field_upserters=[
                RolePermissionUpserter(entity_type=EntityType(entity_type), permission=bit)
                for entity_type, mask in sorted(self.permissions.items())
                for bit in mask
            ],
            field_purgers=[
                RolePermissionUngrantedPurger(
                    grants={
                        EntityType(entity_type): mask
                        for entity_type, mask in self.permissions.items()
                    }
                )
            ]
            if self.permissions
            else [],
            granted_users=self.users,
        )

    @override
    def check(self) -> list[str]:
        """The rule the create API applies to the name."""
        if not self.name.strip():
            return ["name is blank"]
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[RoleSeed]]) -> list[SeedRejection]:
        """The files granting on a name that is not an entity type: the column takes any
        string."""
        declared = PermissionKinds().declared()
        unknown_by_source: dict[str, set[str]] = defaultdict(set)
        for file in files:
            for seed in file.items:
                unknown_by_source[file.source].update(set(seed.permissions) - declared)
        return [
            SeedRejection(source, f"{', '.join(sorted(unknown))} is not an entity type")
            for source, unknown in sorted(unknown_by_source.items())
            if unknown
        ]
