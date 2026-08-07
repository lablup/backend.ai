"""Searcher implementations for the idle checker repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.engine import Row

from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData, IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.repositories.base.searcher import Searcher


@dataclass
class IdleCheckerSearcher(Searcher[IdleCheckerRow, IdleCheckerData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(IdleCheckerRow)

    @override
    def to_data(self, row: Row[Any]) -> IdleCheckerData:
        checker_row: IdleCheckerRow = row.IdleCheckerRow
        return checker_row.to_data()


@dataclass
class IdleCheckerAssignmentSearcher(Searcher[IdleCheckerBindingRow, IdleCheckerAssignmentData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(IdleCheckerBindingRow)

    @override
    def to_data(self, row: Row[Any]) -> IdleCheckerAssignmentData:
        binding_row: IdleCheckerBindingRow = row.IdleCheckerBindingRow
        return binding_row.to_data()
