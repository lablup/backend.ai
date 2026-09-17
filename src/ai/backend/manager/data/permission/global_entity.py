from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.manager.errors.permission import GlobalEntityMissing, GlobalEntityNotLoaded

__all__ = (
    "GlobalEntityIDCache",
    "global_entity_id",
)


class GlobalEntityIDCache:
    """The id of each global entity, loaded once when the manager starts."""

    _ids: ClassVar[Mapping[GlobalEntityName, GlobalEntityID] | None] = None

    @classmethod
    def fill(cls, ids: Mapping[GlobalEntityName, GlobalEntityID]) -> None:
        missing = [name for name in GlobalEntityName if name not in ids]
        if missing:
            raise GlobalEntityMissing(f"No global entity is named {', '.join(missing)}.")
        cls._ids = dict(ids)

    @classmethod
    def clear(cls) -> None:
        cls._ids = None

    @classmethod
    def id_of(cls, name: GlobalEntityName) -> GlobalEntityID:
        if cls._ids is None:
            raise GlobalEntityNotLoaded(f"Read the id of {name} before the ids are loaded.")
        return cls._ids[name]


def global_entity_id(name: GlobalEntityName) -> GlobalEntityID:
    return GlobalEntityIDCache.id_of(name)
