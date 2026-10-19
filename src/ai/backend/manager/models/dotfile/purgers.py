from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.dotfile.searchable_fields import DotfileSearchableFields
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


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
        return DotfileSearchableFields.own.to_data(row)
