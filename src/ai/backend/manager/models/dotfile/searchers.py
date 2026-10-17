from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class DotfileSearcher(Searcher[DotfileRow, DotfileData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DotfileRow)

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()
