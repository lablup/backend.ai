"""List-read spec for entity invitations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class EntityShareSearcher(Searcher[EntityShareRow, EntityShareData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EntityShareRow)

    @override
    def to_data(self, row: EntityShareRow) -> EntityShareData:
        return row.to_data()
