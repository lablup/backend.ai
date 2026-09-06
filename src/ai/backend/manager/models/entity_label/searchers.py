"""Searcher implementation for the label repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = ("EntityLabelSearcher",)


@dataclass
class EntityLabelSearcher(Searcher[EntityLabelRow, EntityLabelData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(EntityLabelRow)

    @override
    def to_data(self, row: EntityLabelRow) -> EntityLabelData:
        return row.to_data()
