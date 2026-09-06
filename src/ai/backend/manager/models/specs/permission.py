"""The role permission entries the permission ops consume and answer.

READ and UPDATE always state a field scope: the bit in ``permission`` means the
operation on every field, a path in ``fields`` carrying the bit means the path and
its descendants, neither means nothing. The other operations carry no scope.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission


@dataclass(frozen=True)
class PermissionKey:
    """One (scope, entity_type) coordinate of a role's permissions."""

    scope: EntityIdentifier
    entity_type: EntityType


@dataclass(frozen=True)
class PermissionEntry:
    """What one key of a role's permissions holds.

    ``fields`` values are READ|UPDATE bits; a bit set both in ``permission`` and
    in a field value is rejected by the ops.
    """

    scope: EntityIdentifier
    entity_type: EntityType
    permission: Permission
    fields: Mapping[FieldPath, Permission] = field(default_factory=dict)

    def key(self) -> PermissionKey:
        return PermissionKey(scope=self.scope, entity_type=self.entity_type)

    def allows(self, operation: Permission, path: FieldPath | None = None) -> bool:
        """Whether ``operation`` (one bit) holds on ``path``; ``None`` asks for the
        operation on every field."""
        if self.permission & operation:
            return True
        if path is None:
            return False
        return any(
            bits & operation and (scoped == path or path.startswith(scoped + "."))
            for scoped, bits in self.fields.items()
        )


@dataclass(frozen=True)
class PermissionRevocation:
    """The bits taken back from one key.

    ``permission`` bits leave the key entirely — a READ or UPDATE bit takes its
    scoped paths with it. ``fields`` bits leave the named paths and their
    descendants; a path covered by an all-fields bit has nothing to remove.
    """

    scope: EntityIdentifier
    entity_type: EntityType
    permission: Permission = Permission.NONE
    fields: Mapping[FieldPath, Permission] = field(default_factory=dict)

    def key(self) -> PermissionKey:
        return PermissionKey(scope=self.scope, entity_type=self.entity_type)
