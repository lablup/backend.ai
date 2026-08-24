"""Searcher implementation for the label repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = ("LabelSearcher",)


@dataclass
class LabelSearcher(Searcher[LabelRow, LabelData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(LabelRow)

    @override
    def to_data(self, row: LabelRow) -> LabelData:
        return row.to_data()
