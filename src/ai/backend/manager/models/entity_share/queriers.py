"""Single-row read spec for entity invitations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class EntityShareQuerier(DataQuerier[EntityShareRow, EntityShareData]):
    share_id: EntityShareID

    @override
    def row_class(self) -> type[EntityShareRow]:
        return EntityShareRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityShareRow.id

    @override
    def entity_id_value(self) -> EntityShareID:
        return self.share_id

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()
