from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass(kw_only=True)
class DefaultDotfileSearcher(Searcher[DotfileRow, DotfileData]):
    entity: EntityIdentifier

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(DotfileRow)
            .where(
                DotfileRow.entity_type == self.entity.entity_type(),
                DotfileRow.entity_id == self.entity,
                DotfileRow.is_default,
            )
            .order_by(DotfileRow.id)
        )

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()
