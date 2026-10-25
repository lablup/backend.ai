from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.global_entity.row import GlobalEntityRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("GlobalEntityUpserter",)


@dataclass
class GlobalEntityUpserter(EntityUpserter[GlobalEntityRow, GlobalEntityID]):
    """Upserter for a singleton scope under its stated id, created in no scope.

    Conflict key: ``name``. A singleton already there keeps its id: other rows point at it.
    """

    id: GlobalEntityID
    name: GlobalEntityName

    @override
    def entity_id(self, row: GlobalEntityRow) -> GlobalEntityID:
        return GlobalEntityID(row.id)

    @override
    def created_in(self, row: GlobalEntityRow) -> Collection[EntityIdentifier]:
        return ()

    @override
    def row_class(self) -> type[GlobalEntityRow]:
        return GlobalEntityRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {}

    @override
    def to_data(self, row: GlobalEntityRow) -> GlobalEntityID:
        return GlobalEntityID(row.id)
