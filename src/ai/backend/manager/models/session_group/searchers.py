"""Searcher specs for the session_groups table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.models.session_group.row import SessionGroupRow
from ai.backend.manager.models.session_group.searchable_fields import SessionGroupSearchableFields
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = ("SessionGroupSearcher",)


@dataclass
class SessionGroupSearcher(Searcher[SessionGroupRow, SessionGroupData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SessionGroupRow)

    @override
    def to_data(self, row: SessionGroupRow) -> SessionGroupData:
        return SessionGroupSearchableFields.own.to_data(row)
