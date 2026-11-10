"""``created_in`` of entities created in the singleton scopes.

Listed before the spec root in the bases, so the mixin's ``created_in`` answers the
root's abstract hook.
"""

from __future__ import annotations

from collections.abc import Collection

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.models.base import Base


class CreatedInGlobal[TRow: Base]:
    """Created in the `global` scope."""

    def created_in(self, row: TRow) -> Collection[EntityIdentifier]:
        return (global_entity_id(GlobalEntityName.GLOBAL),)


class CreatedInPublic[TRow: Base]:
    """Created in the `global` and `public` scopes."""

    def created_in(self, row: TRow) -> Collection[EntityIdentifier]:
        return (
            global_entity_id(GlobalEntityName.GLOBAL),
            global_entity_id(GlobalEntityName.PUBLIC),
        )
