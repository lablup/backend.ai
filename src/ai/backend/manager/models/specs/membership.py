"""The membership and grant records the entity writes carry to the ops layer."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.types import Permission


@dataclass(frozen=True)
class EntityMembershipEntry:
    """A member entity under the entity it joins."""

    member: EntityIdentifier
    parent: EntityIdentifier


@dataclass(frozen=True)
class EntityGrant:
    """One existing entity shared into a grantee's scope, bounded by a cap.

    Where :class:`EntityMembershipEntry` states belonging settled at creation, this
    states access handed out afterwards and taken back later. ``permission_cap`` is
    the ceiling the grantee's own permissions are clipped to; ``None`` clips nothing.
    """

    entity: EntityIdentifier
    grantee: EntityIdentifier
    permission_cap: Permission | None = None
