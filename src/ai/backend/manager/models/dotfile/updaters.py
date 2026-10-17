from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.dotfile.types import DotfileData, DotfileEntries, DotfileEntry
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater


@dataclass
class DefaultDotfileUpdater(DataBatchUpdater[DotfileRow, DotfileData]):
    entity: EntityIdentifier
    path: str
    updater: DotfileEntryUpdater

    @property
    @override
    def row_class(self) -> type[DotfileRow]:
        return DotfileRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [
            lambda: DotfileRow.entity_type == self.entity.entity_type(),
            lambda: DotfileRow.entity_id == self.entity,
            lambda: DotfileRow.is_default.is_(True),
            lambda: DotfileRow.path == self.path,
        ]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"perm": self.updater.perm, "data": self.updater.data}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()


@dataclass(frozen=True)
class DotfileEntryUpdater:
    """Describe an edit to a default file."""

    perm: str
    data: str

    def apply(self, current: DotfileEntries, path: str) -> DotfileEntries:
        return current.replaced(DotfileEntry(path=path, perm=self.perm, data=self.data))
