"""Searcher implementations for the idle checker repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class IdleCheckerSearcher(Searcher[IdleCheckerRow, IdleCheckerData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(IdleCheckerRow)

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()
