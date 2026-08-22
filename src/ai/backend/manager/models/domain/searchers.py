"""Searcher specs for the domains table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class DomainSearcher(Searcher[DomainRow, DomainData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DomainRow)

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()
