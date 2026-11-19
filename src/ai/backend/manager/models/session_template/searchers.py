"""Searcher implementations for the session template repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.session_template.types import SessionTemplateData
from ai.backend.manager.models.session_template.row import SessionTemplateRow
from ai.backend.manager.models.session_template.searchable_fields import (
    SessionTemplateSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class SessionTemplateSearcher(Searcher[SessionTemplateRow, SessionTemplateData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SessionTemplateRow)

    @override
    def to_data(self, row: SessionTemplateRow) -> SessionTemplateData:
        return SessionTemplateSearchableFields.own.to_data(row)
