from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater


@dataclass
class DotfileUpdater(DataUpdater[DotfileRow, DotfileData]):
    """Rewrite one dotfile, named by its own id."""

    dotfile_id: DotfileID
    perm: str
    data: str

    @property
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
    def build_values(self) -> dict[str, Any]:
        return {"perm": self.perm, "data": self.data}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()
