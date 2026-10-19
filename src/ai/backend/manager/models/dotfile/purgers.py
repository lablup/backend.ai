from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.purger import FieldBatchPurger, FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


class UserDotfilePurger(FieldBatchPurger[EntityIdentifier, DotfileRow, DotfileData]):
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


@dataclass
class DotfilePurger(FieldPurger[DotfileRow, DotfileData]):
    """Remove one dotfile, named by its own id."""

    dotfile_id: DotfileID

    @override
    def row_class(self) -> type[DotfileRow]:
        return DotfileRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DotfileRow.id

    @override
    def target_id_value(self) -> DotfileID:
        return self.dotfile_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()
