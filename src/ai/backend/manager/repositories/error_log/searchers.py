"""Searcher implementations for the error log repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.models.error_logs import ErrorLogRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ErrorLogSearcher(Searcher[ErrorLogRow, ErrorLogData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ErrorLogRow)

    @override
    def to_data(self, row: ErrorLogRow) -> ErrorLogData:
        return row.to_dataclass()
