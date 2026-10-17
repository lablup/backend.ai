from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.dotfile.types import DotfileData, DotfileEntries
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck


class DotfilePurger(FieldBatchPurger[EntityIdentifier, DotfileRow, DotfileData]):
    @override
    def build_subquery(self, owner_id: EntityIdentifier) -> sa.sql.Select[Any]:
        return sa.select(DotfileRow).where(
            DotfileRow.entity_type == owner_id.entity_type(),
            DotfileRow.entity_id == owner_id,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()


@dataclass(frozen=True)
class DefaultDotfilePurger(FieldBatchPurger[EntityIdentifier, DotfileRow, DotfileData]):
    """Remove the default variant of one path."""

    path: str

    @override
    def build_subquery(self, owner_id: EntityIdentifier) -> sa.sql.Select[Any]:
        return sa.select(DotfileRow).where(
            DotfileRow.entity_type == owner_id.entity_type(),
            DotfileRow.entity_id == owner_id,
            DotfileRow.path == self.path,
            DotfileRow.is_default,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()


@dataclass(frozen=True)
class DotfileEntryPurger:
    path: str

    def apply(self, current: DotfileEntries) -> DotfileEntries:
        return current.removed(self.path)
