from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.querier import OwnedFieldQuerier


@dataclass
class DotfileQuerier(OwnedFieldQuerier[EntityIdentifier, DotfileRow, DotfileData]):
    entity_type: EntityType
    conditions: Sequence[QueryCondition]

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DotfileRow).where(
            DotfileRow.entity_type == self.entity_type,
            *(condition() for condition in self.conditions),
        )

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return DotfileRow.entity_id

    @override
    def to_data(self, row: DotfileRow) -> DotfileData:
        return row.to_data()
