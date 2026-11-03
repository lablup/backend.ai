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

    _ids_by_name: ClassVar[Mapping[GlobalEntityName, GlobalEntityID] | None] = None
    _names_by_id: ClassVar[Mapping[GlobalEntityID, GlobalEntityName] | None] = None

    @classmethod
    def fill(cls, ids_by_name: Mapping[GlobalEntityName, GlobalEntityID]) -> None:
        missing = [name for name in GlobalEntityName if name not in ids_by_name]
        if missing:
            raise GlobalEntityMissing(f"No global entity is named {', '.join(missing)}.")
        cls._ids_by_name = dict(ids_by_name)
        cls._names_by_id = {entity_id: name for name, entity_id in ids_by_name.items()}

    @classmethod
    def clear(cls) -> None:
        cls._ids_by_name = None
        cls._names_by_id = None

    @classmethod
    def id_of(cls, name: GlobalEntityName) -> GlobalEntityID:
        if cls._ids_by_name is None:
            raise GlobalEntityNotLoaded(f"Read the id of {name} before the ids are loaded.")
        return cls._ids_by_name[name]

    @classmethod
    def name_of(cls, id_: GlobalEntityID) -> GlobalEntityName:
        if cls._names_by_id is None:
            raise GlobalEntityNotLoaded(f"Read the name of {id_} before the ids are loaded.")
        name = cls._names_by_id.get(id_)
        if name is None:
            raise GlobalEntityMissing(f"No global entity has the id {id_}.")
        return name


def global_entity_id(name: GlobalEntityName) -> GlobalEntityID:
    return GlobalEntityIDCache.id_of(name)
