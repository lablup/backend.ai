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
    _names: ClassVar[Mapping[GlobalEntityID, GlobalEntityName] | None] = None

    @classmethod
    def fill(cls, ids: Mapping[GlobalEntityName, GlobalEntityID]) -> None:
        missing = [name for name in GlobalEntityName if name not in ids]
        if missing:
            raise GlobalEntityMissing(f"No global entity is named {', '.join(missing)}.")
        cls._ids = dict(ids)
        cls._names = {id_: name for name, id_ in ids.items()}

    @classmethod
    def clear(cls) -> None:
        cls._ids = None
        cls._names = None

    @classmethod
    def id_of(cls, name: GlobalEntityName) -> GlobalEntityID:
        if cls._ids is None:
            raise GlobalEntityNotLoaded(f"Read the id of {name} before the ids are loaded.")
        return cls._ids[name]

    @classmethod
    def name_of(cls, id_: GlobalEntityID) -> GlobalEntityName:
        if cls._names is None:
            raise GlobalEntityNotLoaded(f"Read the name of {id_} before the ids are loaded.")
        name = cls._names.get(id_)
        if name is None:
            raise GlobalEntityMissing(f"No global entity has the id {id_}.")
        return name


def global_entity_id(name: GlobalEntityName) -> GlobalEntityID:
    return GlobalEntityIDCache.id_of(name)
