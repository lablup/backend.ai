"""The membership records the entity writes carry to the ops layer."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.data.entity.types import EntityIdentifier


@dataclass(frozen=True)
class EntityMembershipEntry:
    """A member entity under the entity it joins."""

    member: EntityIdentifier
    parent: EntityIdentifier
