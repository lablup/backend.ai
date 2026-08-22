"""Searcher specs for the groups table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ProjectSearcher(Searcher[ProjectRow, ProjectData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ProjectRow)

    @override
    def to_data(self, row: ProjectRow) -> ProjectData:
        return row.to_data()
