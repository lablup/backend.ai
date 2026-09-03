"""The membership and grant records the entity writes carry to the ops layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.permission.id import FieldPath
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
    the ceiling on every field; a share always states one, zero included. A path
    in ``fields`` carrying a READ or UPDATE bit caps that operation on the path
    and its descendants, so its bits never appear in ``permission_cap``.
    """

    entity: EntityIdentifier
    grantee: EntityIdentifier
    permission_cap: Permission
    fields: Mapping[FieldPath, Permission] = field(default_factory=dict)
