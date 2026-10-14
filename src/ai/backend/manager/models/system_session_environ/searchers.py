from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("SystemSessionEnvironSearcher",)


@dataclass
class SystemSessionEnvironSearcher(Searcher[SystemSessionEnvironRow, SystemSessionEnvironData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SystemSessionEnvironRow)

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return row.to_data()
